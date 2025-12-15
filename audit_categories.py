# audit_categories.py — Full metrics definition
AUDIT_CATEGORIES = {
    "Performance": {
        "desc": "Measures speed, responsiveness, and optimization of the website.",
        "metrics": [
            "First Contentful Paint", "Largest Contentful Paint", "Cumulative Layout Shift",
            "Speed Index", "Time to Interactive", "Total Blocking Time",
            "Server Response Time", "Resource Compression", "Image Optimization"
        ]
    },
    "Security": {
        "desc": "Checks security standards and vulnerability risks.",
        "metrics": [
            "HTTPS Enabled", "Secure Cookies", "Content Security Policy",
            "No Mixed Content", "XSS Protection", "SQL Injection Protection",
            "Password Strength Enforcement", "CSRF Protection", "Firewall Active"
        ]
    },
    "Accessibility": {
        "desc": "Evaluates website accessibility for all users.",
        "metrics": [
            "Alt Text on Images", "Contrast Ratio", "ARIA Roles",
            "Keyboard Navigation", "Form Labels", "Error Identification",
            "Heading Structure", "Link Purpose Clear", "Page Language Specified"
        ]
    },
    "SEO": {
        "desc": "Search engine optimization compliance.",
        "metrics": [
            "Meta Description", "Title Tag Length", "Heading Tags",
            "Canonical Tags", "XML Sitemap", "Robots.txt Presence",
            "Mobile Friendly", "Structured Data", "Alt Attributes for Images"
        ]
    },
    "Best Practices": {
        "desc": "General best practices for modern websites.",
        "metrics": [
            "HTTPS Redirects", "No Deprecated APIs", "Responsive Design",
            "Error Page Handling", "Favicon Present", "Console Errors Free",
            "Secure External Scripts", "Lazy Loading", "Clean Code Structure"
        ]
    }
}
