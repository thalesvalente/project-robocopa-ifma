"""Finite connection budgets; no sockets or engine needed in these tests."""
import unittest
from services.worker_agent.arena_protocol import SessionBudget, BudgetLimits, ProtocolDenied

class SessionBudgetTests(unittest.TestCase):
    def setUp(self):
        self.now=0.0;self.clock=lambda:self.now
    def test_exact_input_limit(self):
        budget=SessionBudget(BudgetLimits(messages=2,input_bytes=4),clock=self.clock)
        budget.accept('ab');budget.accept('cd')
        with self.assertRaisesRegex(ProtocolDenied,'MESSAGE_BUDGET'):budget.accept('')
    def test_total_bytes_utf8(self):
        budget=SessionBudget(BudgetLimits(input_bytes=4),clock=self.clock)
        budget.accept('á')
        with self.assertRaisesRegex(ProtocolDenied,'INPUT_BUDGET'):budget.accept('áa')
    def test_output_budget(self):
        budget=SessionBudget(BudgetLimits(output_bytes=4),clock=self.clock)
        budget.accept_output('1234')
        with self.assertRaisesRegex(ProtocolDenied,'OUTPUT_BUDGET'):budget.accept_output('5')
    def test_idle_timeout(self):
        budget=SessionBudget(BudgetLimits(idle_seconds=2,lifetime_seconds=10),clock=self.clock)
        self.now=2.1
        with self.assertRaisesRegex(ProtocolDenied,'IDLE_LIMIT'):budget.wait_timeout()
    def test_absolute_lifetime_despite_activity(self):
        budget=SessionBudget(BudgetLimits(idle_seconds=2,lifetime_seconds=3),clock=self.clock)
        self.now=1;budget.accept('a');self.now=2;budget.accept('a');self.now=3.1
        with self.assertRaisesRegex(ProtocolDenied,'SESSION_LIMIT'):budget.wait_timeout()
    def test_timeout_positive_and_bounded(self):
        budget=SessionBudget(BudgetLimits(idle_seconds=2,lifetime_seconds=3),clock=self.clock)
        self.assertEqual(budget.wait_timeout(),2)
        self.now=1.5;budget.accept('a');self.assertEqual(budget.wait_timeout(),1.5)
    def test_invalid_limits(self):
        for kwargs in ({'messages':0},{'input_bytes':-1},{'output_bytes':True},{'lifetime_seconds':float('inf')},{'idle_seconds':0}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):BudgetLimits(**kwargs)
    def test_binary_and_surrogate_denied(self):
        for value in (b'bad','\ud800'):
            with self.subTest(type=type(value)),self.assertRaises(ProtocolDenied):SessionBudget().accept(value)
