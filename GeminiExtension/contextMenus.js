chrome.runtime.onMessage.addListener(
    function (request, sender, sendResponse) {
        if (request.type === "getSelectedText") {
            chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
                chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    function: function () {
                        try {
                            return window.getSelection().toString();
                        } catch (error) {
                            console.error("Lỗi khi lấy văn bản:", error);
                            return "";
                        }
                    }
                }, function (results) {
                    if (results && results.length > 0 && results[0].result) {
                        sendResponse({ selectedText: results[0].result });
                    } else {
                        sendResponse({ selectedText: "" });
                    }
                });
            });
            return true;
        }
    }
);
