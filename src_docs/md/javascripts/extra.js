// Custom JavaScript for claif_cla documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add copy buttons to code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(function(block) {
        const button = document.createElement('button');
        button.className = 'md-clipboard md-icon';
        button.title = 'Copy to clipboard';
        button.innerHTML = '<svg viewBox="0 0 24 24"><path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"></path></svg>';
        
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent).then(function() {
                button.title = 'Copied!';
                setTimeout(function() {
                    button.title = 'Copy to clipboard';
                }, 2000);
            });
        });
        
        block.parentNode.appendChild(button);
    });
});