document.getElementById('saveBtn').addEventListener('click', () => {
    const apiKey = document.getElementById('apiKey').value;
    const selectedModel = document.getElementById('modelInput').value;
    const encryptedApiKey = btoa(apiKey);
    chrome.storage.local.set({ geminiApiKey: encryptedApiKey, geminiModel: selectedModel }, () => {
        alert('API Key và Model đã được lưu.');
        window.close();
    });
});

// Hiển thị model hiện tại khi popup được mở
chrome.storage.local.get(['geminiModel'], (result) => {
    const currentModel = result.geminiModel || 'gemini-2.0-flash-exp';
    document.getElementById('currentModelName').textContent = currentModel;
    document.getElementById('modelInput').value = currentModel;
});
