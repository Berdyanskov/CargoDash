import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import Editor from "@monaco-editor/react";
import { useEffect, useRef } from "react";
export function CodeField({ label, value, onChange, height = 160 }) {
    const wrapperRef = useRef(null);
    // Block keyboard events from bubbling up past Monaco to ancestor
    // listeners (e.g. React Flow's document-level keyboard handlers).
    // IMPORTANT: bubble phase, not capture. Capture-phase stopPropagation
    // would prevent Monaco itself from seeing keys like Tab (browser default
    // shifts focus). We let Monaco handle the key first, then stop the
    // bubble so document-level listeners don't see it.
    useEffect(() => {
        const el = wrapperRef.current;
        if (!el)
            return;
        const stop = (e) => e.stopPropagation();
        el.addEventListener("keydown", stop, false);
        el.addEventListener("keyup", stop, false);
        el.addEventListener("keypress", stop, false);
        return () => {
            el.removeEventListener("keydown", stop, false);
            el.removeEventListener("keyup", stop, false);
            el.removeEventListener("keypress", stop, false);
        };
    }, []);
    const onMount = (editor) => {
        // Ensure the editor immediately accepts keyboard input on first click,
        // and explicitly override indentation options so they can't drift from
        // some other source (e.g. detected indent from default value).
        editor.updateOptions({
            tabSize: 4,
            insertSpaces: true,
            useTabStops: false,
            detectIndentation: false,
        });
    };
    return (_jsxs("div", { className: "space-y-1", children: [_jsx("div", { className: "text-[11px] uppercase tracking-wide text-slate-400", children: label }), _jsx("div", { ref: wrapperRef, className: "border rounded overflow-hidden", 
                // Also block at the React synthetic layer for good measure.
                onKeyDown: (e) => e.stopPropagation(), onKeyUp: (e) => e.stopPropagation(), children: _jsx(Editor, { height: height, defaultLanguage: "python", value: value, onChange: (v) => onChange(v ?? ""), onMount: onMount, options: {
                        minimap: { enabled: false },
                        fontSize: 12,
                        lineNumbers: "off",
                        scrollBeyondLastLine: false,
                        tabSize: 4,
                        insertSpaces: true,
                        detectIndentation: false,
                        quickSuggestions: false,
                        suggestOnTriggerCharacters: false,
                        wordBasedSuggestions: "off",
                        acceptSuggestionOnEnter: "off",
                        acceptSuggestionOnCommitCharacter: false,
                        tabCompletion: "off",
                        parameterHints: { enabled: false },
                        useTabStops: false,
                        autoIndent: "keep",
                    } }) })] }));
}
