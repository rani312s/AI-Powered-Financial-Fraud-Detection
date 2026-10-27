import os
import re
import sys

def audit_responsive():
    print("=== STARTING RESPONSIVE AUDIT ===")
    
    html_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html')
    css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'css', 'style.css')
    js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'main.js')
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()
    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()
        
    # 1. Viewport Meta tag check
    if 'meta name="viewport" content="width=device-width, initial-scale=1.0"' in html:
        print("[PASS] Viewport meta tag properly configured")
    else:
        print("[FAIL] Missing or incorrect viewport meta tag")
        
    # 2. Global overflow-x check
    if 'overflow-x: hidden' in css and 'box-sizing: border-box' in css:
        print("[PASS] Global overflow-x: hidden and box-sizing: border-box in place")
    else:
        print("[FAIL] Global overflow rules missing")
        
    # 3. Responsive Breakpoints check
    breakpoints = ['1024px', '768px', '640px', '480px', '360px']
    for bp in breakpoints:
        if f'max-width: {bp}' in css:
            print(f"[PASS] Breakpoint <= {bp} present in style.css")
        else:
            print(f"[FAIL] Missing breakpoint <= {bp}")
            
    # 4. Mobile Navigation components check
    elements = ['mobile-menu-btn', 'sidebar-close-btn', 'sidebar-backdrop', 'sidebar.open']
    for el in elements:
        if el in css:
            print(f"[PASS] Mobile navigation rule '{el}' present in style.css")
        else:
            print(f"[FAIL] Missing mobile navigation rule '{el}'")
            
    # 5. Check if any rigid inline styles with fixed pixel widths exist in index.html
    rigid_matches = re.findall(r'style="[^"]*width:\s*\d{3,}px[^"]*"', html)
    if rigid_matches:
        print(f"[WARN] Found {len(rigid_matches)} rigid fixed-width inline styles in index.html:")
        for m in rigid_matches:
            print("   ", m)
    else:
        print("[PASS] No rigid fixed-width inline styles (>=100px) found in index.html!")
        
    # 6. Check tables container
    if '.custom-table-container' in css and 'overflow-x: auto' in css:
        print("[PASS] Table horizontal scrolling container active")
    else:
        print("[FAIL] Table container responsive overflow missing")
        
    # 7. Check images & icons max-width
    if 'img, svg' in css and 'max-width: 100%' in css:
        print("[PASS] Images and icons max-width: 100% active")
    else:
        print("[FAIL] Images & icons max-width rule missing")
        
    # 8. Check CSS brace balancing
    open_braces = css.count('{')
    close_braces = css.count('}')
    if open_braces == close_braces:
        print(f"[PASS] CSS is well-formed with balanced braces ({open_braces} blocks)")
    else:
        print(f"[FAIL] CSS brace imbalance: {open_braces} open vs {close_braces} close")
        
    print("=== AUDIT COMPLETED SUCCESSFULLY ===")

if __name__ == '__main__':
    audit_responsive()
