// Initialize Mermaid with custom configuration
window.addEventListener('DOMContentLoaded', (event) => {
    mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        themeVariables: {
            primaryColor: '#8bc34a',
            primaryTextColor: '#fff',
            primaryBorderColor: '#689f38',
            lineColor: '#689f38',
            secondaryColor: '#c5e1a5',
            tertiaryColor: '#dcedc8'
        },
        flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
        },
        sequence: {
            useMaxWidth: true,
            mirrorActors: true
        },
        gantt: {
            useMaxWidth: true
        }
    });
});
