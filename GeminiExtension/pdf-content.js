let lastSelectedText = '';
let mousePosition = { x: 0, y: 0 };

// Lưu vị trí chuột
document.addEventListener('mousemove', function(e) {
    mousePosition.x = e.clientX;
    mousePosition.y = e.clientY;
});

// Theo dõi text được chọn
document.addEventListener('mouseup', function(e) {
    lastSelectedText = window.getSelection().toString().trim();
});

// Lắng nghe message từ background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getSelectedText") {
        sendResponse({ 
            text: lastSelectedText,
            mouseX: mousePosition.x,
            mouseY: mousePosition.y
        });
    }
    return true; // Quan trọng để xử lý bất đồng bộ
});

// Thêm style cho popup
const style = document.createElement('style');
style.textContent = `
    #geminiResult {
        position: fixed;
        z-index: 10000;
        background-color: white;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        max-width: 300px;
        font-size: 14px;
        max-height: 200px;
        overflow-y: auto;
    }
`;
document.head.appendChild(style); 