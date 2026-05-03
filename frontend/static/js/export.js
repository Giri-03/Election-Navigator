/**
 * ExportManager — generates CSV and plain text downloads from checklist state.
 * Uses the JS Blob API for client-side download (no server round-trip).
 * Filename: election-checklist-{state}-{date}.csv
 * Requirements: Export feature
 */

const ExportManager = (() => {
  let _btnExport = null;
  let _getSteps  = null; // function that returns current steps array
  let _getState  = null; // function that returns current state string

  function init(getStepsFn, getStateFn) {
    _btnExport = document.getElementById('btn-export');
    _getSteps  = getStepsFn;
    _getState  = getStateFn;

    _btnExport.addEventListener('click', _onExportClick);
  }

  function _onExportClick() {
    const steps = _getSteps ? _getSteps() : [];
    const state = (_getState ? _getState() : 'india').replace(/\s+/g, '-').toLowerCase();
    const date  = new Date().toISOString().slice(0, 10);

    if (steps.length === 0) {
      alert('No checklist to export yet. Complete the onboarding first.');
      return;
    }

    const csv  = _toCSV(steps);
    _download(csv, `election-checklist-${state}-${date}.csv`, 'text/csv');
  }

  function _toCSV(steps) {
    const header = ['Step', 'Description', 'Importance', 'Action', 'Status'];
    const rows = steps.map((s, i) => [
      _csvCell(`${i + 1}. ${s.title}`),
      _csvCell(s.description),
      _csvCell(s.importance),
      _csvCell(s.action),
      _csvCell(s.status === 'done' ? 'Done' : 'Pending'),
    ]);
    return [header.join(','), ...rows.map(r => r.join(','))].join('\r\n');
  }

  function _csvCell(val) {
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
  }

  function _download(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return { init };
})();
