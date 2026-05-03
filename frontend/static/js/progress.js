/**
 * ProgressBar — computes journey completion % and updates the UI bar.
 * Requirements: Progress Bar feature
 */

const ProgressBar = (() => {
  let _fill = null;
  let _pct  = null;

  function init() {
    _fill = document.getElementById('progress-fill');
    _pct  = document.getElementById('progress-pct');
  }

  /**
   * Update the progress bar.
   * @param {Array} steps - [{status: 'done'|'pending', ...}, ...]
   */
  function update(steps) {
    if (!steps || steps.length === 0) {
      _set(0);
      return;
    }
    const completed = steps.filter(s => s.status === 'done').length;
    const pct = Math.round((completed / steps.length) * 100);
    _set(pct);
  }

  function _set(pct) {
    const clamped = Math.min(100, Math.max(0, pct));
    if (_fill) _fill.style.width = `${clamped}%`;
    if (_pct)  _pct.textContent  = `${clamped}%`;
  }

  return { init, update };
})();
