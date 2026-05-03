/**
 * WhatIfPanel — activates alert mode when status === 'what_if' or 'not_eligible'.
 * Switches left panel to alert styling, shows alert banner, replaces checklist
 * with recovery steps. "Back to main flow" button restores normal state.
 * Requirements: 5.1–5.5
 */

const WhatIfPanel = (() => {
  let _panelLeft   = null;
  let _alertBanner = null;
  let _alertTitle  = null;
  let _alertMsg    = null;
  let _btnBack     = null;
  let _onBack      = null; // callback to restore normal dashboard

  function init(onBackCallback) {
    _panelLeft   = document.getElementById('panel-left');
    _alertBanner = document.getElementById('alert-banner');
    _alertTitle  = document.getElementById('alert-title');
    _alertMsg    = document.getElementById('alert-message');
    _btnBack     = document.getElementById('btn-back-flow');
    _onBack      = onBackCallback;

    _btnBack.addEventListener('click', deactivate);
  }

  /**
   * Activate alert mode with the given response data.
   * @param {Object} data - NavigatorResponse with status 'what_if' or 'not_eligible'
   */
  function activate(data) {
    _panelLeft.classList.add('alert-mode');

    _alertTitle.textContent = data.status === 'not_eligible'
      ? '⚠ Not Eligible'
      : '⚠ Issue Detected';
    _alertMsg.textContent = data.message || '';

    _alertBanner.style.display = 'flex';
    _alertBanner.style.flexDirection = 'column';
  }

  /** Restore normal dashboard state. */
  function deactivate() {
    _panelLeft.classList.remove('alert-mode');
    _alertBanner.style.display = 'none';
    if (_onBack) _onBack();
  }

  return { init, activate, deactivate };
})();
