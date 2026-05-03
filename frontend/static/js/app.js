/**
 * app.js — main entry point.
 * Wires all JS modules together and manages screen transitions.
 * Every /chat_flow response updates: timeline, checklist, progress,
 * confidence meter, and left panel status simultaneously.
 * Requirements: 7.1, 1.2
 */

(() => {
  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------
  let _currentState = null; // last profile state string
  let _lastTimeline = [];   // last timeline data (for re-render on back)

  // Client-side profile accumulator — updated as each answer is accepted
  const _profile = {
    age: null,
    citizenship: null,
    state: null,
    first_time_voter: null,
    has_voter_id: null,
  };

  // Field order matches backend QUESTIONS sequence
  const FIELD_ORDER = ['age', 'citizenship', 'state', 'first_time_voter', 'has_voter_id'];
  let _nextFieldIndex = 0; // which field was just answered

  // -----------------------------------------------------------------------
  // Screen helpers
  // -----------------------------------------------------------------------
  function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
  }

  // -----------------------------------------------------------------------
  // Profile summary (left panel)
  // -----------------------------------------------------------------------
  function updateProfileSummary() {
    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = (val !== null && val !== undefined) ? val : '—';
    };
    set('p-age',   _profile.age);
    set('p-state', _profile.state);
    set('p-ftv',   _profile.first_time_voter !== null
      ? (_profile.first_time_voter ? 'Yes' : 'No') : '—');
    set('p-hid',   _profile.has_voter_id !== null
      ? (_profile.has_voter_id ? 'Yes' : 'No') : '—');
    _currentState = _profile.state || '';
  }

  /**
   * Called by OnboardingEngine after each accepted answer so the left
   * panel updates in real time as the user progresses.
   * @param {string} rawAnswer - the raw string the user typed/clicked
   * @param {number} fieldIndex - index into FIELD_ORDER that was just filled
   */
  function recordAnswer(rawAnswer, fieldIndex) {
    const field = FIELD_ORDER[fieldIndex];
    if (!field) return;
    switch (field) {
      case 'age':
        _profile.age = parseInt(rawAnswer, 10) || rawAnswer;
        break;
      case 'citizenship':
        _profile.citizenship = ['yes','y','indian','india'].includes(rawAnswer.toLowerCase())
          ? 'Indian' : 'Other';
        break;
      case 'state':
        _profile.state = rawAnswer;
        break;
      case 'first_time_voter':
        _profile.first_time_voter = ['yes','y','true','1'].includes(rawAnswer.toLowerCase());
        break;
      case 'has_voter_id':
        _profile.has_voter_id = ['yes','y','true','1'].includes(rawAnswer.toLowerCase());
        break;
    }
    updateProfileSummary();
  }

  // -----------------------------------------------------------------------
  // Status badge
  // -----------------------------------------------------------------------
  function updateStatusBadge(status) {
    const badge = document.getElementById('status-badge');
    if (!badge) return;
    badge.className = 'status-badge';
    if (status === 'eligible' || status === 'complete') {
      badge.classList.add('eligible');
      badge.textContent = '✓ Eligible';
    } else if (status === 'not_eligible') {
      badge.classList.add('not-eligible');
      badge.textContent = '✗ Not Eligible';
    } else {
      badge.classList.add('eligible');
      badge.textContent = 'In Progress';
    }
  }

  // -----------------------------------------------------------------------
  // Full dashboard update from a NavigatorResponse
  // -----------------------------------------------------------------------
  function applyResponse(data) {
    updateStatusBadge(data.status);

    // Timeline
    if (data.timeline && data.timeline.length > 0) {
      _lastTimeline = data.timeline;
      TimelineRenderer.render(data.timeline, 'registration');
    }

    // Alert mode (what_if / not_eligible)
    if (data.status === 'what_if' || data.status === 'not_eligible') {
      WhatIfPanel.activate(data);
      ChecklistRenderer.render(data.steps || []);
      ProgressBar.update(data.steps || []);
      ConfidenceMeter.update(data.steps || []);
      return;
    }

    // Normal eligible/complete flow
    WhatIfPanel.deactivate();

    if (data.steps && data.steps.length > 0) {
      ChecklistRenderer.render(data.steps);
    }

    ProgressBar.update(ChecklistRenderer.getSteps());
    ConfidenceMeter.update(ChecklistRenderer.getSteps());
  }

  // -----------------------------------------------------------------------
  // Step toggle callback — recalculate progress + confidence client-side
  // -----------------------------------------------------------------------
  function onStepToggle(steps) {
    ProgressBar.update(steps);
    ConfidenceMeter.update(steps);
  }

  // -----------------------------------------------------------------------
  // Onboarding complete callback
  // -----------------------------------------------------------------------
  function onProfileComplete(data) {
    showScreen('screen-dashboard');
    updateProfileSummary();
    applyResponse(data);
  }

  // -----------------------------------------------------------------------
  // Start Over — reset session and return to landing
  // -----------------------------------------------------------------------
  async function startOver() {
    try {
      await fetch('/reset', { method: 'POST' });
    } catch (_) { /* ignore network errors on reset */ }
    // Reset local profile state
    Object.keys(_profile).forEach(k => { _profile[k] = null; });
    _nextFieldIndex = 0;
    _lastTimeline = [];
    _currentState = null;
    updateProfileSummary();
    showScreen('screen-landing');
  }

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', () => {
    // Init all modules
    TimelineRenderer.init();
    ChecklistRenderer.init(onStepToggle);
    ProgressBar.init();
    ConfidenceMeter.init();
    WhatIfPanel.init(() => {
      // Back to main flow: re-render last known good state
      if (_lastTimeline.length > 0) TimelineRenderer.render(_lastTimeline, 'registration');
      ProgressBar.update(ChecklistRenderer.getSteps());
      ConfidenceMeter.update(ChecklistRenderer.getSteps());
    });
    ExportManager.init(
      () => ChecklistRenderer.getSteps(),
      () => _currentState || 'india'
    );
    OnboardingEngine.init(onProfileComplete, recordAnswer);

    // Landing CTA
    document.getElementById('btn-start').addEventListener('click', () => {
      showScreen('screen-onboarding');
      OnboardingEngine.startFirstQuestion();
    });

    // Start Over button (injected into left panel)
    const startOverBtn = document.createElement('button');
    startOverBtn.className = 'btn-start-over';
    startOverBtn.textContent = '↺ Start Over';
    startOverBtn.addEventListener('click', startOver);
    document.getElementById('panel-left').appendChild(startOverBtn);
  });
})();
