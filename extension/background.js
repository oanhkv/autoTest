// background.js — service worker.
// Cấu hình để BẤM ICON extension sẽ MỞ SIDE PANEL (cửa sổ bên cạnh web, không mất khi click trang).
chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});

// Phòng trường hợp service worker khởi động lại
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
