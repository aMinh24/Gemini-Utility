chrome.contextMenus.create({
    id: "explainText",
    title: "Giải thích văn bản này",
    contexts: ["selection"],
    documentUrlPatterns: ["*://*/*", "file://*"]
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    try {
        if (!tab || tab.id === -1) {
            const [currentTab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!currentTab) {
                console.error("Không thể tìm thấy tab hiện tại");
                return;
            }
            tab = currentTab;
        }

        if (info.menuItemId === "explainText") {
            const selectedText = info.selectionText;
            if (selectedText) {
                chrome.storage.local.get(['geminiApiKey'], async (result) => {
                    let apiKey = result.geminiApiKey;
                    if (!apiKey) {
                        // Mở popup để nhập API key
                        chrome.windows.create({
                            url: 'popup.html',
                            type: 'popup',
                            width: 400,
                            height: 200
                        });
                        return;
                    }
                    try {
                        apiKey = atob(apiKey);
                        if (!apiKey) {
                            console.error("Không thể giải mã API key.");
                            return;
                        }
                        explainText(selectedText, tab, apiKey);
                    } catch (error) {
                        console.error("Lỗi giải mã API key:", error);
                        return;
                    }
                });
            }
        }
    } catch (error) {
        console.error("Lỗi khi xử lý context menu:", error);
    }
});

async function explainText(text, tab, apiKey) {
    const model = await new Promise(resolve => {
        chrome.storage.local.get(['geminiModel'], result => {
            resolve(result.geminiModel || 'gemini-2.0-flash-exp');
        });
    });
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;
    const prompt = `Giải thích ngắn gọn văn bản sau bằng tiếng việt: ${text}`;

    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-goog-api-key': apiKey
        },
        body: JSON.stringify({
            contents: [{
                parts: [{
                    text: prompt
                }]
            }]
        })
    })
    .then(response => response.json())
    .then(async data => {
        const result = data.candidates?.[0]?.content?.parts?.[0]?.text || "Lỗi giải thích.";
        try {
            await injectAndShowResult(result, tab);
        } catch (error) {
            console.error("Lỗi khi hiển thị kết quả:", error);
        }
    })
    .catch(error => {
        console.error("Lỗi:", error);
        injectAndShowResult("Lỗi giải thích.", tab).catch(console.error);
    });
}

async function injectAndShowResult(result, tab) {
    try {
        // Inject CSS
        await chrome.scripting.insertCSS({
            target: { tabId: tab.id },
            css: `
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
                    color: black;
                }
                #geminiResult .close-button {
                    position: absolute;
                    right: 5px;
                    top: 5px;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: #ff4444;
                    color: white;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    line-height: 1;
                }
                #geminiResult .content {
                    margin-top: 10px;
                    padding-right: 20px;
                }
            `
        });

        // Lấy vị trí chuột và hiển thị kết quả
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: (result) => {
                const mouseX = window.mouseX || window.event?.clientX || 100;
                const mouseY = window.mouseY || window.event?.clientY || 100;

                // Xóa popup cũ nếu tồn tại
                const oldPopup = document.getElementById('geminiResult');
                if (oldPopup) {
                    oldPopup.remove();
                }

                // Tạo popup mới
                const popup = document.createElement('div');
                popup.id = 'geminiResult';

                // Tạo nút đóng
                const closeButton = document.createElement('button');
                closeButton.className = 'close-button';
                closeButton.innerHTML = '×';
                closeButton.onclick = () => {
                    popup.remove();
                };

                // Tạo phần nội dung
                const content = document.createElement('div');
                content.className = 'content';
                content.textContent = result;

                // Thêm các phần tử vào popup
                popup.appendChild(closeButton);
                popup.appendChild(content);

                // Đặt vị trí popup
                popup.style.left = mouseX + 'px';
                popup.style.top = (mouseY - 10) + 'px';
                
                document.body.appendChild(popup);
            },
            args: [result]
        });
    } catch (error) {
        console.error("Lỗi khi inject script:", error);
        throw error;
    }
}
