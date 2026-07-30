import React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { ArrowUp, Mic, Paperclip, StopCircle, X } from "lucide-react";
import { motion } from "framer-motion";

type PromptAttachment = {
  id: string;
  name: string;
  size: number;
};

type PromptInputBoxProps = {
  value: string;
  onValueChange: (value: string) => void;
  onSend: () => void;
  onToggleRecording: () => void;
  onTranscribeRecording?: () => void;
  onAttachFiles?: (files: File[]) => void;
  onRemoveAttachment?: (id: string) => void;
  onPaste?: React.ClipboardEventHandler<HTMLTextAreaElement>;
  attachments?: PromptAttachment[];
  isRecording?: boolean;
  isLoading?: boolean;
  hasRecordingReady?: boolean;
  micLevel?: number;
  placeholder?: string;
  sendLabel?: string;
  className?: string;
};

function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${Math.round(size / 1024)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export const PromptInputBox = React.forwardRef<HTMLDivElement, PromptInputBoxProps>(
  (
    {
      value,
      onValueChange,
      onSend,
      onToggleRecording,
      onTranscribeRecording,
      onAttachFiles,
      onRemoveAttachment,
      onPaste,
      attachments = [],
      isRecording = false,
      isLoading = false,
      hasRecordingReady = false,
      micLevel = 0.12,
      placeholder = "Speak naturally, or write a quick note.",
      sendLabel = "Save transcript",
      className,
    },
    ref,
  ) => {
    const fileInputRef = React.useRef<HTMLInputElement | null>(null);
    const textareaRef = React.useRef<HTMLTextAreaElement | null>(null);
    const hasText = value.trim().length > 0;
    const waveformBars = React.useMemo(
      () =>
        Array.from({ length: 26 }, (_, index) => {
          const swing = Math.sin(index * 0.82 + micLevel * 9);
          return Math.max(0.18, Math.min(1, micLevel * 1.25 + (swing + 1) * 0.2));
        }),
      [micLevel],
    );

    React.useEffect(() => {
      if (!textareaRef.current) {
        return;
      }
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 220)}px`;
    }, [value]);

    function handleSubmit(): void {
      if (isLoading || !hasText) {
        return;
      }
      onSend();
    }

    function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>): void {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        handleSubmit();
      }
    }

    function handleFiles(files: FileList | null): void {
      const selected = files ? Array.from(files) : [];
      if (selected.length > 0) {
        onAttachFiles?.(selected);
      }
    }

    return (
      <TooltipPrimitive.Provider delayDuration={180}>
        <div ref={ref} className={cn("ai-prompt-box", isRecording && "ai-prompt-box--recording", className)}>
          {attachments.length > 0 ? (
            <div className="ai-prompt-box__attachments" aria-label="Attached files">
              {attachments.map((attachment) => (
                <span key={attachment.id} className="ai-prompt-box__attachment">
                  <Paperclip aria-hidden="true" />
                  <span>{attachment.name}</span>
                  <small>{formatBytes(attachment.size)}</small>
                  <button type="button" onClick={() => onRemoveAttachment?.(attachment.id)} aria-label={`Remove ${attachment.name}`}>
                    <X aria-hidden="true" />
                  </button>
                </span>
              ))}
            </div>
          ) : null}

          <div className={cn("ai-prompt-box__input-wrap", isRecording && "ai-prompt-box__input-wrap--hidden")}>
            <textarea
              ref={textareaRef}
              className="ai-prompt-box__textarea"
              value={value}
              onChange={(event) => onValueChange(event.target.value)}
              onPaste={onPaste}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              rows={1}
              disabled={isLoading || isRecording}
            />
          </div>

          <div className={cn("ai-prompt-box__recorder", isRecording && "ai-prompt-box__recorder--active")} aria-hidden={!isRecording}>
            <div className="ai-prompt-box__recording-status">
              <span />
              Recording
            </div>
            <div className="ai-prompt-box__waveform">
              {waveformBars.map((bar, index) => (
                <motion.span
                  key={index}
                  animate={{ scaleY: isRecording ? bar : 0.2 }}
                  transition={{ duration: 0.18, ease: "easeOut" }}
                  style={{ transformOrigin: "center" }}
                />
              ))}
            </div>
          </div>

          <div className="ai-prompt-box__footer">
            <div className="ai-prompt-box__left-actions">
              <TooltipPrimitive.Root>
                <TooltipPrimitive.Trigger asChild>
                  <button
                    className="ai-prompt-box__icon-button"
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading || isRecording || !onAttachFiles}
                    aria-label="Attach file"
                  >
                    <Paperclip aria-hidden="true" />
                  </button>
                </TooltipPrimitive.Trigger>
                <TooltipPrimitive.Portal>
                  <TooltipPrimitive.Content className="ai-prompt-box__tooltip" sideOffset={6}>
                    Attach file
                    <TooltipPrimitive.Arrow className="ai-prompt-box__tooltip-arrow" />
                  </TooltipPrimitive.Content>
                </TooltipPrimitive.Portal>
              </TooltipPrimitive.Root>
              <input
                ref={fileInputRef}
                className="sr-only"
                type="file"
                multiple
                onChange={(event) => {
                  handleFiles(event.target.files);
                  event.target.value = "";
                }}
              />
              {hasRecordingReady && onTranscribeRecording ? (
                <button className="ai-prompt-box__transcribe" type="button" onClick={onTranscribeRecording} disabled={isLoading}>
                  {isLoading ? "Transcribing..." : "Transcribe"}
                </button>
              ) : null}
            </div>

            <div className="ai-prompt-box__right-actions">
              <TooltipPrimitive.Root>
                <TooltipPrimitive.Trigger asChild>
                  <button
                    className={cn("ai-prompt-box__voice-button", isRecording && "ai-prompt-box__voice-button--recording")}
                    type="button"
                    onClick={onToggleRecording}
                    disabled={isLoading}
                    aria-label={isRecording ? "Stop recording" : "Start recording"}
                  >
                    {isRecording ? <StopCircle aria-hidden="true" /> : <Mic aria-hidden="true" />}
                  </button>
                </TooltipPrimitive.Trigger>
                <TooltipPrimitive.Portal>
                  <TooltipPrimitive.Content className="ai-prompt-box__tooltip" sideOffset={6}>
                    {isRecording ? "Stop recording" : "Start recording"}
                    <TooltipPrimitive.Arrow className="ai-prompt-box__tooltip-arrow" />
                  </TooltipPrimitive.Content>
                </TooltipPrimitive.Portal>
              </TooltipPrimitive.Root>

              <TooltipPrimitive.Root>
                <TooltipPrimitive.Trigger asChild>
                  <button className="ai-prompt-box__send-button" type="button" onClick={handleSubmit} disabled={isLoading || !hasText}>
                    <ArrowUp aria-hidden="true" />
                    <span className="sr-only">{sendLabel}</span>
                  </button>
                </TooltipPrimitive.Trigger>
                <TooltipPrimitive.Portal>
                  <TooltipPrimitive.Content className="ai-prompt-box__tooltip" sideOffset={6}>
                    {sendLabel}
                    <TooltipPrimitive.Arrow className="ai-prompt-box__tooltip-arrow" />
                  </TooltipPrimitive.Content>
                </TooltipPrimitive.Portal>
              </TooltipPrimitive.Root>
            </div>
          </div>
        </div>
      </TooltipPrimitive.Provider>
    );
  },
);

PromptInputBox.displayName = "PromptInputBox";
