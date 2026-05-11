import Editor, { type OnMount } from "@monaco-editor/react";
import { useEffect, useRef } from "react";

interface Props {
  label: string;
  value: string;
  onChange: (next: string) => void;
  height?: number;
}

export function CodeField({ label, value, onChange, height = 160 }: Props) {
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Block keyboard events from bubbling up to ancestor listeners (e.g. React
  // Flow's document-level keyboard handlers). Use the native capture phase
  // because React's onKeyDownCapture still fires after the browser has
  // dispatched the event to document-level listeners.
  useEffect(() => {
    const el = wrapperRef.current;
    if (!el) return;
    const stop = (e: KeyboardEvent) => e.stopPropagation();
    el.addEventListener("keydown", stop, true);
    el.addEventListener("keyup", stop, true);
    el.addEventListener("keypress", stop, true);
    return () => {
      el.removeEventListener("keydown", stop, true);
      el.removeEventListener("keyup", stop, true);
      el.removeEventListener("keypress", stop, true);
    };
  }, []);

  const onMount: OnMount = (editor) => {
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

  return (
    <div className="space-y-1">
      <div className="text-[11px] uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div
        ref={wrapperRef}
        className="border rounded overflow-hidden"
        // Also block at the React synthetic layer for good measure.
        onKeyDown={(e) => e.stopPropagation()}
        onKeyUp={(e) => e.stopPropagation()}
      >
        <Editor
          height={height}
          defaultLanguage="python"
          value={value}
          onChange={(v) => onChange(v ?? "")}
          onMount={onMount}
          options={{
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
          }}
        />
      </div>
    </div>
  );
}
