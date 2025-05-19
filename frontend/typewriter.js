function typewriterEffect(elementId, text, speed = 30) {
  const element = document.getElementById(elementId);
  let i = 0;
  element.innerHTML = '';
  
  // Create cursor element
  const cursor = document.createElement('span');
  cursor.className = 'typewriter-cursor';
  cursor.innerHTML = '|';
  element.appendChild(cursor);
  
  function type() {
    if (i < text.length) {
      // Insert character before cursor
      element.insertBefore(document.createTextNode(text.charAt(i)), cursor);
      i++;
      setTimeout(type, speed);
    } else {
      // Remove cursor when done
      element.removeChild(cursor);
    }
  }
  
  type();
}