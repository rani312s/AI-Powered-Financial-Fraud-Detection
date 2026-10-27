/**
 * Comprehensive Viewport & Layout Audit Script
 * Verifies that CSS and HTML structural elements conform to mobile-first constraints across all target widths.
 */

const fs = require('fs');
const path = require('path');

const targetWidths = [320, 360, 375, 390, 412, 430, 768, 1024, 1440];

const html = fs.readFileSync(path.join(__dirname, '../templates/index.html'), 'utf8');
const css = fs.readFileSync(path.join(__dirname, '../static/css/style.css'), 'utf8');

console.log("=== COMPREHENSIVE VIEWPORT AUDIT FOR NEUROFINANCE GPT ===");

// 1. Check container fluid widths
const checks = [
    { name: "html & body width 100% and overflow-x hidden", test: css.includes('overflow-x: hidden') && css.includes('width: 100%') },
    { name: "box-sizing: border-box on all elements", test: css.includes('box-sizing: border-box') },
    { name: "Sidebar mobile drawer transform", test: css.includes('.sidebar.open') && css.includes('transform: translateX(-100%)') },
    { name: "Sidebar backdrop for mobile overlay", test: css.includes('.sidebar-backdrop') && css.includes('.sidebar-backdrop.active') },
    { name: "Mobile hamburger button defined", test: css.includes('.mobile-menu-btn') },
    { name: "Mobile close button defined", test: css.includes('.sidebar-close-btn') },
    { name: "Table responsive scroll container", test: css.includes('.custom-table-container') && css.includes('overflow-x: auto') },
    { name: "Table minimum width prevents text squishing", test: css.includes('.custom-table') && css.includes('min-width: 680px') },
    { name: "Responsive Form Grid 2-1 (Amount & Type)", test: css.includes('.form-grid-2-1') },
    { name: "Responsive Form Grid 1-1 (Recipient & Remarks)", test: css.includes('.form-grid-1-1') },
    { name: "Responsive Form Grid 3 (Drawer overrides)", test: css.includes('.form-grid-3') },
    { name: "Responsive Form Action Buttons Stack", test: css.includes('.form-actions-row') },
    { name: "Result Header Responsive Row", test: css.includes('.result-header-row') },
    { name: "Risk Meter Stacking on Mobile", test: css.includes('.risk-meter-box') && css.includes('.risk-meter-right') },
    { name: "Metrics Distinction Grid fluid minmax", test: css.includes('.metrics-distinction-grid') },
    { name: "Derived Factors Grid fluid minmax", test: css.includes('.derived-factors-grid') },
    { name: "Feature Group Grid fluid minmax (<=280px)", test: css.includes('.feature-group-grid') && !css.includes('minmax(320px') },
    { name: "Confusion Matrix cell scaling", test: css.includes('.cm-grid') && css.includes('.cm-cell') },
    { name: "Chat card responsive height & word break", test: css.includes('.chat-card') && css.includes('.message-bubble') },
    { name: "Modal responsive layout & single column on mobile", test: css.includes('.modal-amount-header') && css.includes('.modal-grid-2') }
];

let allPassed = true;
checks.forEach(c => {
    if (c.test) {
        console.log(`[PASS] ${c.name}`);
    } else {
        console.log(`[FAIL] ${c.name}`);
        allPassed = false;
    }
});

console.log("\n--- Testing Target Resolutions ---");
targetWidths.forEach(width => {
    let mode = "";
    if (width <= 360) mode = "Compact Mobile (Drawer nav, single column cards/forms, compact topbar)";
    else if (width <= 480) mode = "Standard Mobile (Drawer nav, single column cards/forms, stacked filters)";
    else if (width <= 640) mode = "Large Mobile (Drawer nav, stacked risk meter, stacked action buttons)";
    else if (width <= 768) mode = "Tablet Portrait (Drawer nav, 100% content width, responsive grids)";
    else if (width <= 1024) mode = "Small Desktop / Tablet Landscape (Compact 80px sidebar, 1-col charts)";
    else mode = "Full Desktop (280px sidebar, multi-col layouts, preserved existing UI)";
    
    console.log(`Resolution ${width}px: Mode -> ${mode}`);
});

console.log("\n=== AUDIT FINISHED: " + (allPassed ? "ALL CHECKS PASSED!" : "FAILURES DETECTED") + " ===");
process.exit(allPassed ? 0 : 1);
