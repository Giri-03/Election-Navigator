/**
 * ChecklistRenderer — renders interactive step cards with Done/Pending toggles.
 * Each card shows title, description, importance badge, action, and toggle.
 * Toggling a step triggers progress/confidence recalculation and a glow pulse.
 * Requirements: 3.1, 6.5
 */

const ChecklistRenderer = (() => {
  let _list = null;
  let _steps = [];          // current step objects (with live status)
  let _onToggle = null;     // callback(steps) fired after any toggle

  function init(onToggleCallback) {
    _list = document.getElementById('checklist-list');
    _onToggle = onToggleCallback;
  }

  /**
   * Render steps array into the checklist container.
   * @param {Array} steps - [{title, description, importance, action, status}, ...]
   */
  function render(steps) {
    _steps = steps.map(s => ({ ...s })); // local copy
    _list.innerHTML = '';

    _steps.forEach((step, i) => {
      const card = _buildCard(step, i);
      _list.appendChild(card);
    });
  }

  function _buildCard(step, index) {
    const card = document.createElement('div');
    card.className = `step-card${step.status === 'done' ? ' done' : ''}`;
    card.dataset.index = index;

    card.innerHTML = `
      <button class="step-toggle" aria-label="Toggle step ${index + 1}" title="Mark as done">
        ${step.status === 'done' ? '✓' : ''}
      </button>
      <div class="step-body">
        <div class="step-top">
          <span class="step-title">${_esc(step.title)}</span>
          <span class="importance-badge ${step.importance}">${step.importance}</span>
        </div>
        <p class="step-desc">${_esc(step.description)}</p>
        <p class="step-action">${_esc(step.action)}</p>
      </div>
    `;

    card.querySelector('.step-toggle').addEventListener('click', () => _toggle(index));
    return card;
  }

  function _toggle(index) {
    const step = _steps[index];
    step.status = step.status === 'done' ? 'pending' : 'done';

    // Re-render just this card
    const oldCard = _list.querySelector(`[data-index="${index}"]`);
    const newCard = _buildCard(step, index);

    if (step.status === 'done') {
      newCard.classList.add('just-done');
      // Remove glow class after animation
      newCard.addEventListener('animationend', () => newCard.classList.remove('just-done'), { once: true });
    }

    _list.replaceChild(newCard, oldCard);

    if (_onToggle) _onToggle([..._steps]);
  }

  /** Return current steps with live statuses (for export / progress calc). */
  function getSteps() {
    return [..._steps];
  }

  function _esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  return { init, render, getSteps };
})();
