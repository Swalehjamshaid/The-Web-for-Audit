# /app/app/audit_categories.py

"""
Defines the structure for website audit categories and their respective metrics.
"""

AUDIT_CATEGORIES = {
    "Performance": {
        "desc": "Measures speed, responsiveness, and optimization using Core Web Vitals and general speed metrics.",
        "metrics": [
            "First Contentful Paint (FCP)", "Largest Contentful Paint (LCP)", "Cumulative Layout Shift (CLS)",
            "Interaction to Next Paint (INP)", "Time to First Byte (TTFB)", "Speed Index",
            "Total Blocking Time (TBT)", "Server Response Time", "Resource Compression (Gzip/Brotli)",
            "Image Optimization and Next-Gen Formats (WebP)", "Minimize Main-Thread Work", "Effective Caching Policy",
        ]
    },
    "Security": {
        "desc": "Checks security standards, vulnerability risks, and secure data handling.",
        "metrics": [
            "HTTPS Enabled (SSL/TLS)", "Secure Cookies (HttpOnly, Secure, SameSite)", "Content Security Policy (CSP) Implemented",
            "No Mixed Content (HTTP and HTTPS resources)", "HSTS (HTTP Strict Transport Security)", "X-Content-Type-Options: nosniff",
            "X-Frame-Options: DENY or SAMEORIGIN", "Input Validation/SQL Injection Prevention", "CSRF (Cross-Site Request Forgery) Protection",
            "Firewall / WAF Active", "Dependency Vulnerability Check",
        ]
    },
    "Accessibility": {
        "desc": "Evaluates website accessibility for all users, including those using assistive technologies (WCAG compliance).",
        "metrics": [
            "Alt Text on All Images (Informative vs. Decorative)", "Minimum Contrast Ratio (4.5:1 or better)", "ARIA Roles and Attributes Correctly Used",
            "Full Keyboard Navigation Support", "Semantic HTML Structure", "Form Labels Associated with Controls",
            "Error Identification and Suggestions", "Heading Structure Logical (<H1> present and unique)", "Page Language Specified (lang attribute)",
            "Non-Text Content Alternatives",
        ]
    },
    "SEO": {
        "desc": "Search engine optimization compliance for indexing and ranking.",
        "metrics": [
            "Meta Description Present and Unique", "Title Tag Length and Relevance", "Heading Tags Hierarchy (H1, H2, H3)",
            "Canonical Tags Correctly Used", "XML Sitemap Presence and Validity", "Robots.txt Presence and Correct Configuration",
            "Mobile Friendly / Viewport Configured", "Structured Data (Schema Markup) Implemented", "Image Alt Attributes for SEO",
            "Broken Links Check (404/410 errors)", "Descriptive URL Structure",
        ]
    },
    "Best Practices": {
        "desc": "General best practices for modern web development, reliability, and code quality.",
        "metrics": [
            "HTTPS Redirects Enforced", "No Deprecated APIs or Frameworks", "Responsive Design (Adapts to different screen sizes)",
            "Custom 404/Error Page Handling", "Favicon Present (all sizes)", "Console Errors and Warnings Free",
            "Third-Party Scripts Scanned for Security", "Lazy Loading for Offscreen Images/Iframes", "HTML Doctype Declared",
            "Transitional/Experimental CSS Properties Check", "Clean Code Structure and Maintainability",
        ]
    }
}
