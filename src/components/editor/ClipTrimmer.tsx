"use client"

import React, { useState, useRef, useEffect } from "react"
import { motion } from "framer-motion"
import {
    Scissors,
    GripVertical,
    Undo2,
    Save,
    Loader2,
    ChevronLeft,
    ChevronRight,
    ZoomIn,
    ZoomOut
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"

interface ClipTrimmerProps {
    clipId: string
    duration: number // in seconds
    trimStart: number
    trimEnd: number | null
    videoUrl?: string
    onTrimChange: (start: number, end: number | null) => void
    onSplit: (splitPoint: number) => void
    onSave: () => void
    isSaving?: boolean
}

export function ClipTrimmer({
    clipId,
    duration,
    trimStart,
    trimEnd,
    videoUrl,
    onTrimChange,
    onSplit,
    onSave,
    isSaving = false
}: ClipTrimmerProps) {
    const [localStart, setLocalStart] = useState(trimStart)
    const [localEnd, setLocalEnd] = useState(trimEnd ?? duration)
    const [currentTime, setCurrentTime] = useState(trimStart)
    const [zoom, setZoom] = useState(1)
    const [isDragging, setIsDragging] = useState<"start" | "end" | "playhead" | null>(null)
    const timelineRef = useRef<HTMLDivElement>(null)
    const videoRef = useRef<HTMLVideoElement>(null)

    // Format time as MM:SS
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
    }

    // Calculate position on timeline
    const getPosition = (time: number) => {
        return (time / duration) * 100 * zoom
    }

    // Handle timeline click/drag
    const handleTimelineInteraction = (e: React.MouseEvent | React.TouchEvent) => {
        if (!timelineRef.current) return

        const rect = timelineRef.current.getBoundingClientRect()
        const clientX = "touches" in e ? e.touches[0].clientX : e.clientX
        const x = clientX - rect.left
        const percent = Math.max(0, Math.min(1, x / rect.width))
        const time = (percent / zoom) * duration

        if (isDragging === "start") {
            const newStart = Math.min(time, localEnd - 0.5)
            setLocalStart(Math.max(0, newStart))
        } else if (isDragging === "end") {
            const newEnd = Math.max(time, localStart + 0.5)
            setLocalEnd(Math.min(duration, newEnd))
        } else if (isDragging === "playhead") {
            setCurrentTime(Math.max(0, Math.min(duration, time)))
            if (videoRef.current) {
                videoRef.current.currentTime = time
            }
        }
    }

    // Sync video with current time
    useEffect(() => {
        if (videoRef.current && !isDragging) {
            videoRef.current.currentTime = currentTime
        }
    }, [currentTime, isDragging])

    // Update parent when trim changes
    useEffect(() => {
        onTrimChange(localStart, localEnd)
    }, [localStart, localEnd])

    const handleSplit = () => {
        if (currentTime > localStart && currentTime < localEnd) {
            onSplit(currentTime)
        }
    }

    const handleReset = () => {
        setLocalStart(0)
        setLocalEnd(duration)
        setCurrentTime(0)
    }

    return (
        <div className="space-y-4 p-4 bg-muted/30 rounded-lg border">
            {/* Video Preview */}
            {videoUrl && (
                <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
                    <video
                        ref={videoRef}
                        src={videoUrl}
                        className="w-full h-full object-contain"
                        onTimeUpdate={(e) => {
                            if (!isDragging) {
                                setCurrentTime(e.currentTarget.currentTime)
                            }
                        }}
                    />
                    <div className="absolute bottom-2 left-2 bg-black/70 px-2 py-1 rounded text-xs text-white font-mono">
                        {formatTime(currentTime)} / {formatTime(duration)}
                    </div>
                </div>
            )}

            {/* Timeline */}
            <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{formatTime(localStart)}</span>
                    <span className="font-medium text-foreground">
                        Duration: {formatTime(localEnd - localStart)}
                    </span>
                    <span>{formatTime(localEnd)}</span>
                </div>

                <div
                    ref={timelineRef}
                    className="relative h-16 bg-muted rounded-lg overflow-hidden cursor-pointer select-none"
                    onMouseMove={handleTimelineInteraction}
                    onMouseUp={() => setIsDragging(null)}
                    onMouseLeave={() => setIsDragging(null)}
                >
                    {/* Full duration bar */}
                    <div className="absolute inset-0 bg-muted" />

                    {/* Selected region */}
                    <div
                        className="absolute top-0 bottom-0 bg-primary/20 border-l-2 border-r-2 border-primary"
                        style={{
                            left: `${getPosition(localStart)}%`,
                            right: `${100 - getPosition(localEnd)}%`,
                        }}
                    />

                    {/* Trim start handle */}
                    <div
                        className="absolute top-0 bottom-0 w-4 bg-primary rounded-l cursor-ew-resize flex items-center justify-center hover:bg-primary/80 transition-colors"
                        style={{ left: `calc(${getPosition(localStart)}% - 8px)` }}
                        onMouseDown={() => setIsDragging("start")}
                    >
                        <GripVertical className="h-4 w-4 text-primary-foreground" />
                    </div>

                    {/* Trim end handle */}
                    <div
                        className="absolute top-0 bottom-0 w-4 bg-primary rounded-r cursor-ew-resize flex items-center justify-center hover:bg-primary/80 transition-colors"
                        style={{ left: `${getPosition(localEnd)}%` }}
                        onMouseDown={() => setIsDragging("end")}
                    >
                        <GripVertical className="h-4 w-4 text-primary-foreground" />
                    </div>

                    {/* Playhead */}
                    <div
                        className="absolute top-0 bottom-0 w-0.5 bg-white cursor-ew-resize z-10"
                        style={{ left: `${getPosition(currentTime)}%` }}
                        onMouseDown={() => setIsDragging("playhead")}
                    >
                        <div className="absolute -top-1 -left-2 w-4 h-4 bg-white rounded-full shadow-lg border-2 border-primary" />
                    </div>

                    {/* Time markers */}
                    <div className="absolute bottom-0 left-0 right-0 h-4 flex items-end justify-between px-2 text-[8px] text-muted-foreground">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <span key={i}>{formatTime((duration / 4) * i)}</span>
                        ))}
                    </div>
                </div>

                {/* Zoom Control */}
                <div className="flex items-center gap-2">
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => setZoom(Math.max(1, zoom - 0.5))}
                        disabled={zoom <= 1}
                    >
                        <ZoomOut className="h-3.5 w-3.5" />
                    </Button>
                    <Slider
                        value={[zoom]}
                        min={1}
                        max={4}
                        step={0.5}
                        onValueChange={([v]) => setZoom(v)}
                        className="flex-1"
                    />
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => setZoom(Math.min(4, zoom + 0.5))}
                        disabled={zoom >= 4}
                    >
                        <ZoomIn className="h-3.5 w-3.5" />
                    </Button>
                </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2">
                <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    onClick={handleReset}
                >
                    <Undo2 className="h-3.5 w-3.5" />
                    Reset
                </Button>

                <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    onClick={handleSplit}
                    disabled={currentTime <= localStart || currentTime >= localEnd}
                >
                    <Scissors className="h-3.5 w-3.5" />
                    Split at {formatTime(currentTime)}
                </Button>

                <div className="flex-1" />

                <Button
                    size="sm"
                    className="gap-1.5"
                    onClick={onSave}
                    disabled={isSaving}
                >
                    {isSaving ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                        <Save className="h-3.5 w-3.5" />
                    )}
                    Save Trim
                </Button>
            </div>
        </div>
    )
}

interface TextOverlayEditorProps {
    overlays: Array<{
        id: string
        text: string
        position_x: number
        position_y: number
        font_size: number
        font_color: string
        background_color: string
        animation: string
    }>
    onAdd: (overlay: Omit<TextOverlayEditorProps["overlays"][0], "id">) => void
    onUpdate: (id: string, overlay: Partial<TextOverlayEditorProps["overlays"][0]>) => void
    onRemove: (id: string) => void
}

export function TextOverlayEditor({
    overlays,
    onAdd,
    onUpdate,
    onRemove
}: TextOverlayEditorProps) {
    const [newText, setNewText] = useState("")
    const [selectedPosition, setSelectedPosition] = useState<"top" | "center" | "bottom">("bottom")
    const [fontSize, setFontSize] = useState(24)
    const [fontColor, setFontColor] = useState("#ffffff")

    const positionMap = {
        top: { x: 50, y: 10 },
        center: { x: 50, y: 50 },
        bottom: { x: 50, y: 90 }
    }

    const handleAdd = () => {
        if (!newText.trim()) return

        onAdd({
            text: newText,
            position_x: positionMap[selectedPosition].x,
            position_y: positionMap[selectedPosition].y,
            font_size: fontSize,
            font_color: fontColor,
            background_color: "rgba(0,0,0,0.5)",
            animation: "fade"
        })
        setNewText("")
    }

    return (
        <div className="space-y-4">
            {/* Existing overlays */}
            {overlays.length > 0 && (
                <div className="space-y-2">
                    {overlays.map((overlay) => (
                        <div
                            key={overlay.id}
                            className="flex items-center gap-2 p-2 bg-muted rounded-lg text-sm"
                        >
                            <span className="flex-1 truncate">{overlay.text}</span>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 text-destructive"
                                onClick={() => onRemove(overlay.id)}
                            >
                                ×
                            </Button>
                        </div>
                    ))}
                </div>
            )}

            {/* Add new overlay */}
            <div className="space-y-3">
                <input
                    type="text"
                    value={newText}
                    onChange={(e) => setNewText(e.target.value)}
                    placeholder="Enter overlay text..."
                    className="w-full px-3 py-2 text-sm border rounded-lg bg-background"
                />

                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Position:</span>
                    {(["top", "center", "bottom"] as const).map((pos) => (
                        <button
                            key={pos}
                            onClick={() => setSelectedPosition(pos)}
                            className={`px-2 py-1 text-xs rounded capitalize ${selectedPosition === pos
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted hover:bg-muted/80"
                                }`}
                        >
                            {pos}
                        </button>
                    ))}
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Size:</span>
                    <Slider
                        value={[fontSize]}
                        min={12}
                        max={48}
                        step={2}
                        onValueChange={([v]) => setFontSize(v)}
                        className="flex-1"
                    />
                    <span className="text-xs w-8 text-right">{fontSize}px</span>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Color:</span>
                    <input
                        type="color"
                        value={fontColor}
                        onChange={(e) => setFontColor(e.target.value)}
                        className="w-8 h-8 rounded cursor-pointer"
                    />
                    <Button
                        size="sm"
                        onClick={handleAdd}
                        disabled={!newText.trim()}
                        className="ml-auto"
                    >
                        Add Overlay
                    </Button>
                </div>
            </div>
        </div>
    )
}
