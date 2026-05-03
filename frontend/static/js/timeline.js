/**
 * TimelineRenderer — renders 4 horizontal milestone nodes from JSON data.
 * Active node glows with --accent-main; completed nodes are filled.
 * Requirements: 4.1, 6.1, 6.3, 6.4
 */

const TimelineRenderer = (() => {
  const LABEL_DISPLAY = {
    registration: 'Register',
    verification:  'Verify',
    polling:       'Poll',
    result:        'Result',
  };

  let _track = null;

  function init() {
    _track = document.getElementById('timeline-track');
  }

  /**
   * Render timeline from an array of milestone objects.
   * @param {Array}  milestones  - [{label, date_range, description}, ...]
   * @param {string} activeLabel - label of the currently active milestone
   */
  function render(milestones, activeLabel = 'registration') {
    if (!_track || !milestones || milestones.length === 0) return;

    _track.innerHTML = '';

    const activeIndex = milestones.findIndex(m => m.label === activeLabel);

    milestones.forEach((m, i) => {
      const isDone   = i < activeIndex;
      const isActive = i === activeIndex;

      const node = document.createElement('div');
      node.className = 'timeline-node';
      if (isDone)   node.classList.add('done');
      if (isActive) node.classList.add('active');

      // Tooltip via title attribute
      node.title = m.description;

      node.innerHTML = `
        <div class="node-circle">${isDone ? '✓' : ''}</div>
        <span class="node-label">${LABEL_DISPLAY[m.label] || m.label}</span>
        <span class="node-date">${m.date_range}</span>
      `;

      _track.appendChild(node);
    });
  }

  return { init, render };
})();
