chrome.runtime.sendMessage({ type: 'getStatus' }, (response) => {
  const dot = document.getElementById('dot');
  const statusText = document.getElementById('statusText');
  if (response && response.connected) {
    dot.className = 'dot connected';
    statusText.textContent = 'Connected to NASR';
  } else {
    dot.className = 'dot disconnected';
    statusText.textContent = 'Disconnected';
  }
});
