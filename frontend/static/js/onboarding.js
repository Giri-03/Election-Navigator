/**
 * OnboardingEngine — drives the question-by-question profile collection screen.
 * Calls /chat_flow, renders one question at a time, updates step dots,
 * handles text and yes/no inputs, shows inline validation errors.
 * Requirements: 1.1, 1.2, 1.5
 */

const OnboardingEngine = (() => {
  // Profile field order matches backend QUESTIONS sequence
  const FIELD_ORDER = ['age', 'citizenship', 'state', 'first_time_voter', 'has_voter_id'];
  const YESNO_FIELDS = new Set(['citizenship', 'first_time_voter', 'has_voter_id']);

  let _currentFieldIndex = 0;
  let _onComplete = null; // callback(responseData) when profile is done
  let _onAnswer   = null; // callback(rawAnswer, fieldIndex) after each accepted answer

  // DOM refs (resolved on init)
  let _dots, _stepNum, _qText, _qHint, _qError;
  let _inputTextRow, _qInput, _btnSubmit;
  let _inputYesnoRow, _yesnoBtns;
  let _questionPanel;

  function init(onCompleteCallback, onAnswerCallback) {
    _onComplete = onCompleteCallback;
    _onAnswer   = onAnswerCallback;

    _dots         = document.querySelectorAll('.step-dot');
    _stepNum      = document.getElementById('q-step');
    _qText        = document.getElementById('q-text');
    _qHint        = document.getElementById('q-hint');
    _qError       = document.getElementById('q-error');
    _inputTextRow = document.getElementById('input-text-row');
    _qInput       = document.getElementById('q-input');
    _btnSubmit    = document.getElementById('btn-submit');
    _inputYesnoRow = document.getElementById('input-yesno-row');
    _yesnoBtns    = document.querySelectorAll('.btn-yesno');
    _questionPanel = document.getElementById('question-panel');

    // Text submit
    _btnSubmit.addEventListener('click', _submitText);
    _qInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') _submitText();
    });

    // Yes/No buttons
    _yesnoBtns.forEach(btn => {
      btn.addEventListener('click', () => _submitAnswer(btn.dataset.value));
    });
  }

  function _submitText() {
    const val = _qInput.value.trim();
    if (!val) {
      _showError('Please enter a value before continuing.');
      return;
    }
    _submitAnswer(val);
  }

  async function _submitAnswer(answer) {
    _clearError();
    _setLoading(true);

    try {
      const res = await fetch('/chat_flow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: answer }),
      });
      const data = await res.json();

      if (data.error) {
        _showError(data.error);
        _setLoading(false);
        return;
      }

      if (data.status === 'profiling') {
        if (data.message && data.message !== 'Got it. One more question.') {
          // Validation error from backend
          _showError(data.message);
          _setLoading(false);
          return;
        }
        // Notify app of accepted answer so profile panel updates
        if (_onAnswer) _onAnswer(answer, _currentFieldIndex);
        // Advance to next question
        _currentFieldIndex++;
        _renderQuestion(data);
      } else {
        // Profile complete — notify app of last answer then hand off
        if (_onAnswer) _onAnswer(answer, _currentFieldIndex);
        if (_onComplete) _onComplete(data);
      }
    } catch (err) {
      _showError('Network error. Please try again.');
    }

    _setLoading(false);
  }

  function _renderQuestion(data) {
    // Animate panel out then in
    _questionPanel.style.animation = 'none';
    _questionPanel.offsetHeight; // reflow
    _questionPanel.style.animation = 'slideUp 0.35s ease';

    const fieldIndex = _currentFieldIndex;
    const field = FIELD_ORDER[fieldIndex] || null;
    const isYesNo = field ? YESNO_FIELDS.has(field) : false;

    // Update step counter
    _stepNum.textContent = fieldIndex + 1;

    // Update question text and hint from backend
    _qText.textContent = data.next_question || 'Almost done…';
    _qHint.textContent = '';

    // Update dots
    _dots.forEach((dot, i) => {
      dot.classList.remove('active', 'done');
      if (i < fieldIndex) dot.classList.add('done');
      else if (i === fieldIndex) dot.classList.add('active');
    });

    // Toggle input type
    if (isYesNo) {
      _inputTextRow.style.display = 'none';
      _inputYesnoRow.style.display = 'flex';
    } else {
      _inputTextRow.style.display = 'flex';
      _inputYesnoRow.style.display = 'none';
      _qInput.value = '';
      _qInput.type = field === 'age' ? 'number' : 'text';
      _qInput.placeholder = field === 'age' ? 'e.g. 25' : 'Type your answer…';
      setTimeout(() => _qInput.focus(), 50);
    }
  }

  function _showError(msg) {
    _qError.textContent = msg;
  }

  function _clearError() {
    _qError.textContent = '';
  }

  function _setLoading(on) {
    _btnSubmit.disabled = on;
    _yesnoBtns.forEach(b => { b.disabled = on; });
  }

  // Called by app.js to kick off the first question
  async function startFirstQuestion() {
    _currentFieldIndex = 0;
    _setLoading(true);    try {
      const res = await fetch('/chat_flow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: '' }),
      });
      const data = await res.json();
      _renderQuestion(data);
    } catch (err) {
      _showError('Could not connect to server. Please refresh.');
    }
    _setLoading(false);
  }

  return { init, startFirstQuestion };
})();
