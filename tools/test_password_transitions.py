import unittest

from run_password_transitions import PHASES, transition_outcome, parse_transitions


def transitions():
    return [{"phase": phase, "kind": "password" if phase.startswith("password") else "text",
             "beforeOwner": "true" if phase.startswith("password") else "false",
             "afterOwner": "true" if phase.startswith("password") else "false",
             "ownersBeforeKeys": ["true" if phase.startswith("password") else "false"] * 13,
             "acceptedEvents": 26} for phase in PHASES]


class PasswordTransitionTests(unittest.TestCase):
    def test_parser_keeps_native_and_global_flags_separate(self):
        rows = parse_transitions("\n".join([
            "FOCUS_DIAGNOSTIC phase=before-private-key viewSecureOwner=false secureInput=false",
            "PASSWORD_TRANSITION begin=password-immediate kind=password settleMS=0 beforeOwner=false",
            "FOCUS_DIAGNOSTIC phase=before-private-key viewSecureOwner=false secureInput=true",
            "PASSWORD_TRANSITION end=password-immediate afterOwner=true acceptedEvents=2"]))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ownersBeforeKeys"], ["false"])
        self.assertEqual(rows[0]["secureInputBeforeKeys"], ["true"])

    def test_missing_phase_is_inconclusive(self):
        self.assertEqual(transition_outcome(transitions()[:-1], 5), "inconclusive")

    def test_missing_task_is_not_a_pass(self):
        self.assertEqual(transition_outcome(transitions(), 4), "inconclusive")

    def test_missing_flag_is_not_a_protection_gap(self):
        rows = transitions()
        rows[2]["beforeOwner"] = "unavailable"
        self.assertEqual(transition_outcome(rows, 5), "inconclusive")

    def test_one_unprotected_password_key_counts_as_a_gap(self):
        rows = transitions()
        rows[2]["ownersBeforeKeys"][0] = "false"
        self.assertEqual(transition_outcome(rows, 5), "protection-state-gap-observed")

    def test_retained_protection_after_text_switch_also_counts(self):
        rows = transitions()
        rows[3]["beforeOwner"] = "true"
        self.assertEqual(transition_outcome(rows, 5), "protection-state-gap-observed")

    def test_complete_flags_and_tasks_are_only_a_control_pass(self):
        self.assertEqual(transition_outcome(transitions(), 5), "protection-state-controls-passed")
