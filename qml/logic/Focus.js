// Close native dropdown popups before their owning page becomes hidden/locked.
function closePopups(item) {
  if (!item) return
  if (item.popupOpen && typeof item.close === "function") item.close()
  var children = item.children || []
  for (var i = 0; i < children.length; i++) closePopups(children[i])
}
