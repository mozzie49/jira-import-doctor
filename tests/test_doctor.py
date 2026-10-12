import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("doctor", ROOT / "scripts/jira_import_doctor.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
BASE = {"importer": "cloud-external-legacy", "project_type": "company-managed", "intent": "create", "parent_scope": "in-file", "log_row_numbering": "unknown"}


def run(csv, log="", **overrides):
    return d.diagnose(csv.encode(), log.encode(), dict(BASE, **overrides))


def codes(report):
    return {f["code"] for f in report["findings"]}


class DoctorTests(unittest.TestCase):
    def test_preserves_repeated_headers_zeros_multiline(self):
        raw = 'Issue ID,Parent,Summary,Labels,Labels,Component,Component,Description\n001,,Root,a,b,c,d,"line one\nline two"\n002,001,Child,e,f,g,h,plain\n'
        report = run(raw)
        self.assertEqual(report['csv']['headers'].count('Labels'), 2)
        self.assertEqual(report['csv']['headers'].count('Component'), 2)
        self.assertEqual(report['csv']['identities'][0]['id'], '001')
        self.assertEqual(report['csv']['identities'][0]['physical_lines'], [2, 3])
        self.assertEqual(report['csv']['identities'][1]['physical_lines'], [4, 4])
        self.assertFalse([f for f in report['findings'] if f['category'] == 'file_defect'])
        parsed = d.parse_csv(raw.encode(), BASE)
        self.assertEqual(parsed[1][0]['values'][3:7], ['a', 'b', 'c', 'd'])
        self.assertEqual(parsed[1][0]['values'][7], 'line one\nline two')

    def test_graph_defects(self):
        report = run('Issue ID,Parent,Summary\n1,,a\n1,,b\n2,1,c\n3,99,d\n4,4,e\n5,6,f\n6,5,g\n')
        self.assertTrue({'DUPLICATE_ID', 'PARENT_AMBIGUOUS', 'PARENT_NOT_IN_FILE', 'SELF_PARENT', 'PARENT_CYCLE'} <= codes(report))
        self.assertEqual(next(f for f in report['findings'] if f['code'] == 'PARENT_CYCLE')['records'], [6, 7])

    def test_opaque_zero_ids(self):
        report = run('Issue ID,Parent,Summary\n001,,a\n2,1,b\n')
        self.assertIn('PARENT_NOT_IN_FILE', codes(report))

    def test_external_parent_not_defect(self):
        report = run('Issue ID,Parent,Summary\n2,PROJ-1,b\n', parent_scope='external-or-mixed')
        f = next(f for f in report['findings'] if f['code'] == 'PARENT_NOT_IN_FILE')
        self.assertEqual(f['category'], 'destination_unknown')

    def test_other_profile_does_not_assert_parent_defect(self):
        report = run('Issue ID,Parent,Summary\n1,1,a\n', importer='data-center')
        self.assertNotEqual(next(f for f in report['findings'] if f['code'] == 'SELF_PARENT')['category'], 'file_defect')

    def test_update_blank_summary_and_repeated_keys_allowed(self):
        report = run('Issue Key,Summary\nABC-1,\nABC-1,changed\n', intent='update')
        self.assertIn('REPEATED_KEY', codes(report))
        self.assertNotIn('EMPTY_CREATE_SUMMARY', codes(report))
        self.assertFalse([f for f in report['findings'] if f['category'] == 'file_defect'])

    def test_update_missing_key(self):
        self.assertIn('UPDATE_KEY_MISSING', codes(run('Summary\nA\n', intent='update')))

    def test_create_blank_summary(self):
        self.assertIn('EMPTY_CREATE_SUMMARY', codes(run('Summary,Issue ID\n,1\n')))

    def test_ambiguous_role_headers(self):
        report = run('Issue ID,Work item ID,Summary\n1,2,a\n')
        self.assertIn('AMBIGUOUS_COLUMN', codes(report))
        self.assertNotIn('id', report['csv']['resolved_columns'])
        report = run('Issue ID,Work item ID,Summary\n1,2,a\n', columns={'id': 2})
        self.assertEqual(report['csv']['identities'][0]['id'], '2')

    def test_explicit_column_mapping(self):
        report = run('Number,Title,Owner\n001,Thing,A\n', columns={'id': 1, 'summary': 2})
        self.assertEqual(report['csv']['resolved_columns']['summary'], 2)
        self.assertNotIn('SUMMARY_MAPPING_UNKNOWN', codes(report))

    def test_csv_encoding_width_and_parse(self):
        self.assertIn('CSV_ENCODING', {f['code'] for f in d.diagnose(b'\xff', b'', BASE)['findings']})
        self.assertIn('CSV_WIDTH', codes(run('Summary,Parent\nThing\n')))
        self.assertFalse(run('Summary\n"unfinished')['csv']['complete'])

    def test_empty_and_blank_headers(self):
        self.assertIn('CSV_EMPTY', codes(run('')))
        self.assertIn('CSV_HEADER_EMPTY', codes(run('\n')))
        self.assertIn('BLANK_HEADER', codes(run('Summary,\na,b\n')))

    def test_malformed_csv_no_missing_parent_certainty(self):
        report = run('Issue ID,Parent,Summary\n1,2,child\n"unfinished')
        self.assertFalse(report['csv']['complete'])
        self.assertNotEqual(next(f for f in report['findings'] if f['code'] == 'PARENT_NOT_IN_FILE')['category'], 'file_defect')

    def test_explicit_external_id(self):
        report = run('Issue ID,Summary\n001,A\n', "ERROR - Error importing issue [externalId='001', summary='A']: validator rejected")
        self.assertEqual(report['log_events'][0]['record'], 1)
        self.assertEqual(report['log_events'][0]['correlation'], 'matched')

    def test_no_nearest_neighbor_attribution(self):
        report = run('Issue ID,Summary\n1,A\n2,B\n', "INFO - Importing work item: [externalId='1', summary='A']\nWARN - Something failed\nINFO - Importing work item: [externalId='2', summary='B']")
        self.assertIsNone(report['log_events'][0]['record'])

    def test_summary_is_only_candidate(self):
        report = run('Summary\nA\n', "WARN - with summary 'A': invalid value")
        self.assertEqual(report['log_events'][0]['correlation'], 'summary_candidate')
        self.assertIsNone(report['log_events'][0]['record'])

    def test_duplicate_summaries_ambiguous(self):
        report = run('Summary\nA\nA\n', "WARN - with summary 'A': invalid value")
        self.assertEqual(report['log_events'][0]['correlation'], 'ambiguous')

    def test_duplicate_id_ambiguous(self):
        report = run('Issue ID,Summary\n1,A\n1,B\n', "ERROR - Issue ID='1' cannot be created")
        self.assertEqual(report['log_events'][0]['correlation'], 'ambiguous')

    def test_no_match_and_generated_autoid(self):
        report = run('Issue ID,Summary\n1,A\n', "ERROR - Error importing issue [externalId='autoid-100001', summary='A']: failed")
        self.assertEqual(report['log_events'][0]['correlation'], 'no_match')
        self.assertIsNone(report['log_events'][0]['record'])

    def test_conflicting_explicit_refs(self):
        report = run('Issue ID,Summary\n1,A\n2,B\n', "ERROR - Error importing issue [externalId='1', summary='B']: failed")
        self.assertEqual(report['log_events'][0]['correlation'], 'conflicting_references')

    def test_custom_field_key_not_source_key(self):
        report = run('Issue Key,Summary\nABC-1,A\n', "WARN - Cannot add value [ Work item ] to CustomField [ABC-1] in Epic Link with summary 'A'. Probably value was in incorrect format")
        self.assertEqual(report['log_events'][0]['correlation'], 'summary_candidate')
        self.assertIn('KNOWN_IMPORTER_SIGNATURE', codes(report))

    def test_explicit_key(self):
        report = run('Issue Key,Summary\nABC-1,A\n', 'ERROR - Issue key=ABC-1 failed')
        self.assertEqual(report['log_events'][0]['record'], 1)

    def test_row_number_requires_convention(self):
        report = run('Summary\nA\nB\n', 'ERROR - Row 2 invalid')
        self.assertEqual(report['log_events'][0]['correlation'], 'numbering_unknown')
        report = run('Summary\nA\nB\n', 'ERROR - Row 2 invalid', log_row_numbering='header-record-1')
        self.assertEqual(report['log_events'][0]['record'], 1)

    def test_multiline_physical_line(self):
        report = run('Summary,Description\nA,"x\ny"\nB,z\n', 'ERROR - CSV row 4 invalid', log_row_numbering='physical-line-1')
        self.assertEqual(report['log_events'][0]['record'], 2)

    def test_cascade_only_hypothesis(self):
        csv = 'Issue ID,Parent,Summary\n1,,Epic\n2,1,Story\n3,2,Subtask\n'
        log = "ERROR - Error importing issue [externalId='1', summary='Epic']: Issue cannot be created; invalid assignee\nERROR - Error importing issue [externalId='2', summary='Story']: Issue doesn't have a valid Parent\nERROR - Error importing issue [externalId='3', summary='Subtask']: Issue doesn't have a valid Parent"
        report = run(csv, log)
        hypotheses = [f for f in report['findings'] if f['code'] == 'POSSIBLE_PARENT_CASCADE']
        self.assertEqual(len(hypotheses), 2)
        self.assertTrue(all(f['category'] == 'inferred_cascade' for f in hypotheses))
        self.assertEqual(hypotheses[1]['ancestor_chain'], [2, 1])
        self.assertNotIn('POSSIBLE_PARENT_CASCADE', codes(run(csv, '')))
        self.assertNotIn('POSSIBLE_PARENT_CASCADE', codes(run(csv, log.replace('Issue cannot be created;', ''))))

    def test_parent_warning_not_root_failure(self):
        csv = 'Issue ID,Parent,Summary\n1,,Epic\n2,1,Child\n'
        log = "WARN - Issue ID='1' invalid assignee\nERROR - Issue ID='2' doesn't have a valid Parent"
        self.assertNotIn('POSSIBLE_PARENT_CASCADE', codes(run(csv, log)))

    def test_summary_parent_format(self):
        report = run('Summary\nExample child\n', "Subtask 'Example child' doesn't have a valid Parent Id selection. Issue will not be created")
        self.assertEqual(report['log_events'][0]['category'], 'parent_error')
        self.assertEqual(report['log_events'][0]['correlation'], 'summary_candidate')

    def test_real_count_shape_316(self):
        csv = 'Issue Key,Summary\n' + ''.join(f'DEMO-{i},Synthetic {i}\n' for i in range(1, 317))
        log = 'WARN - 270 of 316 work items have been skipped because they already exist in destination projects.\nINFO - 0 out of 316 work items successfully created\nINFO - 46 out of 316 work items successfully updated'
        report = run(csv, log, intent='update')
        self.assertEqual(report['reconciliation']['status'], 'arithmetically_reconciled')
        self.assertFalse(report['reconciliation']['destination_verified'])
        self.assertTrue(all(e['record'] is None for e in report['log_events']))
        self.assertIn('EXISTING_ITEMS_SKIPPED', codes(report))

    def test_synthetic_out_of_skipped_counter(self):
        csv = 'Issue ID,Summary\n001,A\nA:2,B\n03,C\n'
        log = 'INFO - 1 out of 3 issues successfully created\nINFO - 0 out of 3 issues successfully updated\nINFO - 2 out of 3 issues have been skipped because they already exist in destination projects.'
        report = run(csv, log)
        self.assertEqual(report['reconciliation']['status'], 'arithmetically_reconciled')
        self.assertEqual(report['reconciliation']['reported_counts'], {'created': 1, 'updated': 0, 'skipped': 2})
        self.assertFalse(report['reconciliation']['destination_verified'])
        self.assertTrue(all(event['record'] is None for event in report['log_events']))
        self.assertEqual(report['verdict'], 'review_required')

    def test_mixed_skip_grammars_do_not_double_count(self):
        report = run('Summary\nA\n', 'INFO - 1 of 1 issues have been skipped\nINFO - 1 out of 1 issues have been skipped')
        self.assertEqual(report['reconciliation']['status'], 'ambiguous_runs')
        self.assertFalse(report['reconciliation']['destination_verified'])

    def test_duplicate_attempt_counters_not_summed(self):
        log = 'INFO - 1 out of 1 issues successfully created\n' * 2
        self.assertEqual(run('Summary\nA\n', log)['reconciliation']['status'], 'ambiguous_runs')

    def test_counter_mismatch_and_incomplete(self):
        log = 'INFO - 2 out of 2 issues successfully created\nINFO - 0 out of 2 issues successfully updated\nWARN - 0 of 2 issues have been skipped'
        self.assertEqual(run('Summary\nA\n', log)['reconciliation']['status'], 'csv_total_mismatch')
        self.assertEqual(run('Summary\nA\n', 'INFO - 1 issues successfully created')['reconciliation']['status'], 'incomplete_counters')

    def test_conflicting_and_overflow_counts(self):
        self.assertEqual(run('Summary\nA\n', 'INFO - 1 out of 1 issues successfully created\nINFO - 0 out of 2 issues successfully updated')['reconciliation']['status'], 'conflicting_totals')
        self.assertEqual(run('Summary\nA\n', 'INFO - 2 out of 1 issues successfully created')['reconciliation']['status'], 'inconsistent_counts')

    def test_new_items_scope(self):
        csv = 'Issue Key,Summary\nABC-1,A\n'
        unrelated = 'INFO - Importing: Users\nINFO - Only new items will be imported'
        self.assertNotIn('CREATE_MODE_UPDATE_INTENT', codes(run(csv, unrelated, intent='update')))
        scoped = 'INFO - Importing: Work Items\nINFO - Only new items will be imported'
        self.assertIn('CREATE_MODE_UPDATE_INTENT', codes(run(csv, scoped, intent='update')))

    def test_token_redaction_every_output_field(self):
        secret = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456'
        csv = f'Issue ID,Summary\n{secret},A\n'
        log = f'ERROR - Issue ID=\'{secret}\' invalid; Authorization: Bearer top-secret-bearer\nWARN - api_key="another-secret" owner=person@example.org https://a.example/path?token=my-secret\nWARN - Cookie: sid=session-secret'
        report = run(csv, log)
        serialized = json.dumps(report) + d.markdown(report)
        for token in [secret, 'top-secret-bearer', 'another-secret', 'person@example.org', 'my-secret', 'session-secret']:
            self.assertNotIn(token, serialized)
        self.assertIn('REDACTED', serialized)

    def test_json_secret_redaction(self):
        text = '{"password": "some-secret", "token":"token-value"}'
        self.assertNotIn('some-secret', d.redact(text))
        self.assertNotIn('token-value', d.redact(text))

    def test_unknown_context_and_invalid_mapping_refused(self):
        for override in [{'intent': 'guess'}, {'columns': {'id': 0}}, {'columns': {'id': 1, 'key': 1}}, {'columns': {'id': 99}}, {'delimiter': '\n'}, {'extra': True}]:
            with self.subTest(override=override), self.assertRaises(ValueError):
                run('Summary\nA\n', **override)

    def test_large_graph_iterative(self):
        raw = 'Issue ID,Parent,Summary\n' + ''.join(f'{i},{i+1},A{i}\n' for i in range(1, 2001)) + '2001,,Last\n'
        self.assertNotIn('PARENT_CYCLE', codes(run(raw)))

    def test_cli_readonly_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)
            (path/'input.csv').write_text('Summary\nA\n')
            (path/'input.log').write_text('')
            (path/'context.json').write_text(json.dumps(BASE))
            originals = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in path.iterdir()}
            args = ['--csv', str(path/'input.csv'), '--log', str(path/'input.log'), '--context', str(path/'context.json'), '--out', str(path/'out')]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(d.main(args), 0)
                self.assertEqual(d.main(args), 2)
            self.assertTrue((path/'out/report.json').is_file())
            self.assertTrue((path/'out/report.md').is_file())
            for name, checksum in originals.items():
                self.assertEqual(hashlib.sha256((path/name).read_bytes()).hexdigest(), checksum)

    def test_quoted_id_whole_match(self):
        csv = 'Issue ID,Parent,Summary\na,,A\na b,,B\nc,a,C\n'
        report = run(csv, "ERROR - Issue ID='a b': Issue cannot be created")
        self.assertEqual(report['log_events'][0]['record'], 2)
        self.assertNotIn('POSSIBLE_PARENT_CASCADE', codes(report))

    def test_unquoted_id_not_truncated_at_slash(self):
        report = run('Issue ID,Summary\na,A\na/b,B\n', 'ERROR - Issue ID=a/b cannot be created')
        self.assertIsNone(report['log_events'][0]['record'])

    def test_cycle_blocks_cascade(self):
        csv = 'Issue ID,Parent,Summary\n1,2,A\n2,1,B\n'
        log = "ERROR - Error importing issue [externalId='1', summary='A']: Issue cannot be created\nERROR - Error importing issue [externalId='2', summary='B']: Issue doesn't have a valid Parent"
        report = run(csv, log)
        self.assertIn('PARENT_CYCLE', codes(report))
        self.assertNotIn('POSSIBLE_PARENT_CASCADE', codes(report))

    def test_missing_id_mapping_not_orphan_defect(self):
        for csv in ['Source Ref,Parent,Summary\n1,,A\n2,1,B\n', 'Issue ID,Work item ID,Parent,Summary\n1,1,,A\n2,2,1,B\n']:
            report = run(csv)
            self.assertIn('ID_MAPPING_UNKNOWN', codes(report))
            self.assertNotIn('PARENT_NOT_IN_FILE', codes(report))

    def test_subobject_failure_not_issue_failure(self):
        csv = 'Issue ID,Parent,Summary\n1,,A\n2,1,B\n'
        log = "ERROR - Issue ID='1': comment cannot be created; issue creation succeeded\nERROR - Issue ID='2': Issue doesn't have a valid Parent"
        report = run(csv, log)
        self.assertNotEqual(report['log_events'][0]['category'], 'creation_failure')
        self.assertNotIn('POSSIBLE_PARENT_CASCADE', codes(report))

    def test_no_markdown_injection(self):
        csv = 'Issue ID,Parent,Summary\n1,"2\n# INJECTED <script>x</script>",A\n'
        report = run(csv, 'WARN - <img src="https://example.test/track"> [click](https://evil.test)')
        md = d.markdown(report)
        self.assertNotIn('\n# INJECTED', md)
        self.assertNotIn('<script>', md)
        self.assertNotIn('<img', md)
        self.assertNotIn('[click](https://evil.test)', md)

    def test_stack_line_not_csv_row(self):
        report = run('Summary\nA\n', 'WARN - module.py line 1 failed', log_row_numbering='data-record-1')
        self.assertEqual(report['log_events'][0]['correlation'], 'no_reference')

    def test_key_not_truncated(self):
        report = run('Issue Key,Summary\nABC-1,A\n', 'ERROR - Issue key=ABC-1-extra failed')
        self.assertIsNone(report['log_events'][0]['record'])

    def test_cascade_traces_are_bounded(self):
        n = 1200
        csv = 'Issue ID,Parent,Summary\n1,,Root\n' + ''.join(f'{i},{i-1},Item {i}\n' for i in range(2, n+1))
        log = "ERROR - Error importing issue [externalId='1', summary='Root']: Issue cannot be created\n" + ''.join(f"ERROR - Error importing issue [externalId='{i}', summary='Item {i}']: Issue doesn't have a valid Parent\n" for i in range(2, n+1))
        report = run(csv, log)
        cascades = [f for f in report['findings'] if f['code'] == 'POSSIBLE_PARENT_CASCADE']
        self.assertEqual(len(cascades), n-1)
        self.assertTrue(all(len(f['ancestor_chain']) <= 32 for f in cascades))
        self.assertEqual(cascades[-1]['ancestor_distance'], n-1)
        self.assertTrue(cascades[-1]['ancestor_chain_truncated'])

    def test_unquoted_colon_id_not_attributed(self):
        report = run('Issue ID,Summary\na,A\na:1,B\n', 'ERROR - Issue ID=a:1: Issue cannot be created')
        self.assertIsNone(report['log_events'][0]['record'])

    def test_decimal_row_not_truncated(self):
        report = run('Summary\nA\n', 'ERROR - Row 1.5: Issue cannot be created', log_row_numbering='data-record-1')
        self.assertIsNone(report['log_events'][0]['record'])

    def test_title_error_phrase_not_an_outcome(self):
        csv = 'Issue ID,Parent,Summary\n1,,Issue cannot be created\n2,1,Child\n'
        log = "WARN - Error importing issue [externalId='1', summary='Issue cannot be created']: optional field invalid\nERROR - Error importing issue [externalId='2', summary='Child']: Issue doesn't have a valid Parent"
        report = run(csv, log)
        self.assertEqual(report['log_events'][0]['record'], 1)
        self.assertEqual(report['log_events'][0]['category'], 'reported_error')
        self.assertNotIn('POSSIBLE_PARENT_CASCADE', codes(report))

    def test_quoted_title_words_stay_out_of_outcome(self):
        report = run("Issue ID,Summary\n1,Can't: Issue cannot be created\n", "WARN - Error importing issue [externalId='1', summary='Can't: Issue cannot be created']: optional field invalid")
        self.assertEqual(report['log_events'][0]['category'], 'reported_error')

    def test_info_title_is_not_error_event(self):
        report = run('Issue ID,Summary\n1,Invalid login\n', "INFO - Importing work item: [externalId='1', summary='Invalid login']")
        self.assertEqual(report['log_events'], [])

    def test_counter_title_not_aggregate_statement(self):
        report = run('Issue ID,Summary\n1,5 issues successfully created\n', "INFO - Importing issue [externalId='1', summary='5 issues successfully created']")
        self.assertEqual(report['reconciliation']['status'], 'unavailable')
        self.assertEqual(report['reconciliation']['events'], [])

    def test_section_and_mode_title_not_statement(self):
        csv = 'Issue ID,Issue Key,Summary\n1,ABC-1,Only new items will be imported\n'
        log = "INFO - Importing issue [externalId='1', summary='Importing: Work Items']\nINFO - Importing issue [externalId='1', summary='Only new items will be imported']"
        self.assertNotIn('CREATE_MODE_UPDATE_INTENT', codes(run(csv, log, intent='update')))

    def test_no_import_ready_verdict(self):
        self.assertEqual(run('Summary\nFine\n')['verdict'], 'review_required')


if __name__ == '__main__':
    unittest.main()
