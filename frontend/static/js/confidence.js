/**
 * ConfidenceMeter — computes weighted voting readiness score and updates the UI.
 * Weights: critical=3, high=2, medium=1  (mirrors backend confidence.py)
 * Requirements: Confidence Meter feature
 */

const ConfidenceMeter = (() => {
  const WEIGHTS = { critical: 3, high: 2, medium: 1 };

  let _fill  = null;
  let _value = null;

  function init() {
    _fill  = document.getElementById('confidence-fill');
    _value = document.getElementById('confidence-value');
  }

  /**
   * Update the confidence meter.
   * @param {Array} steps - [{importance, status}, ...]
   */
  function update(steps) {
    if (!steps || steps.length === 0) {
      _set(0);
      return;
    }

    const maxWeight = steps.reduce((sum, s) => sum + (WEIGHTS[s.importance] || 1), 0);
    if (maxWeight === 0) { _set(0); return; }

    const earned = steps
      .filter(s => s.status === 'done')
      .reduce((sum, s) => sum + (WEIGHTS[s.importance] || 1), 0);

    const pct = Math.round((earned / maxWeight) * 100);
    _set(pct);
  }

  function _set(pct) {
    const clamped = Math.min(100, Math.max(0, pct));
    if (_fill)  _fill.style.width    = `${clamped}%`;
    if (_value) _value.textContent   = `${clamped}%`;
  }

  return { init, update };
})();
