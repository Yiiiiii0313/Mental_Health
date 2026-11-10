<template>
  <div class="dynamic-bg" :class="{ contained }" aria-hidden="true">
    <div class="bg-base"></div>
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
    <div class="blob blob-4"></div>

    <div class="emoji-layer">
      <span
        v-for="e in emojis"
        :key="e.id"
        class="emoji-deco"
        :class="e.anim"
        :style="{
          left: e.x + '%',
          top: e.y + '%',
          fontSize: e.size + 'px',
          animationDelay: e.delay + 's',
          animationDuration: e.duration + 's',
          opacity: e.opacity,
        }"
      >{{ e.emoji }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  contained: { type: Boolean, default: false },
})

/** 温暖治愈的 emoji 装饰，固定分布避免刷新跳动 */
const emojis = [
  { id: 1, emoji: '💗', anim: 'drift-a', x: 6, y: 8, size: 36, delay: 0, duration: 14, opacity: 0.75 },
  { id: 2, emoji: '🌸', anim: 'float-a', x: 18, y: 5, size: 28, delay: 1.2, duration: 16, opacity: 0.8 },
  { id: 3, emoji: '✨', anim: 'twinkle', x: 32, y: 12, size: 22, delay: 0.5, duration: 10, opacity: 0.9 },
  { id: 4, emoji: '🎵', anim: 'wiggle', x: 48, y: 6, size: 30, delay: 2, duration: 12, opacity: 0.7 },
  { id: 5, emoji: '💗', anim: 'drift-b', x: 62, y: 10, size: 34, delay: 0.8, duration: 18, opacity: 0.72 },
  { id: 6, emoji: '🌼', anim: 'float-b', x: 78, y: 8, size: 26, delay: 3, duration: 15, opacity: 0.78 },
  { id: 7, emoji: '🫶', anim: 'bounce', x: 92, y: 14, size: 32, delay: 1.5, duration: 13, opacity: 0.8 },
  { id: 8, emoji: '😊', anim: 'float-c', x: 4, y: 22, size: 38, delay: 2.5, duration: 17, opacity: 0.65 },
  { id: 9, emoji: '🦋', anim: 'drift-a', x: 15, y: 28, size: 28, delay: 0.3, duration: 20, opacity: 0.75 },
  { id: 10, emoji: '⭐', anim: 'twinkle', x: 28, y: 24, size: 20, delay: 4, duration: 9, opacity: 0.85 },
  { id: 11, emoji: '🌺', anim: 'wiggle', x: 42, y: 20, size: 24, delay: 1.8, duration: 14, opacity: 0.7 },
  { id: 12, emoji: '💕', anim: 'float-a', x: 55, y: 26, size: 30, delay: 2.2, duration: 16, opacity: 0.76 },
  { id: 13, emoji: '🌻', anim: 'drift-b', x: 70, y: 22, size: 32, delay: 0.6, duration: 19, opacity: 0.72 },
  { id: 14, emoji: '☁️', anim: 'float-b', x: 85, y: 30, size: 36, delay: 3.5, duration: 22, opacity: 0.6 },
  { id: 15, emoji: '✨', anim: 'twinkle', x: 96, y: 25, size: 18, delay: 1, duration: 8, opacity: 0.9 },
  { id: 16, emoji: '🌈', anim: 'drift-c', x: 8, y: 42, size: 34, delay: 2.8, duration: 21, opacity: 0.68 },
  { id: 17, emoji: '🪷', anim: 'float-c', x: 22, y: 48, size: 28, delay: 0.9, duration: 15, opacity: 0.74 },
  { id: 18, emoji: '💫', anim: 'twinkle', x: 36, y: 40, size: 22, delay: 3.2, duration: 11, opacity: 0.82 },
  { id: 19, emoji: '🎶', anim: 'wiggle', x: 50, y: 45, size: 26, delay: 1.4, duration: 13, opacity: 0.7 },
  { id: 20, emoji: '🌷', anim: 'float-a', x: 64, y: 38, size: 30, delay: 4.5, duration: 17, opacity: 0.76 },
  { id: 21, emoji: '🧸', anim: 'bounce', x: 76, y: 44, size: 32, delay: 0.4, duration: 14, opacity: 0.7 },
  { id: 22, emoji: '💕', anim: 'drift-a', x: 90, y: 42, size: 24, delay: 2.6, duration: 18, opacity: 0.78 },
  { id: 23, emoji: '🌸', anim: 'float-b', x: 12, y: 58, size: 26, delay: 3.8, duration: 16, opacity: 0.8 },
  { id: 24, emoji: '🕊️', anim: 'drift-b', x: 30, y: 55, size: 30, delay: 1.6, duration: 20, opacity: 0.65 },
  { id: 25, emoji: '⭐', anim: 'twinkle', x: 45, y: 62, size: 20, delay: 0.7, duration: 10, opacity: 0.88 },
  { id: 26, emoji: '🫧', anim: 'float-c', x: 58, y: 58, size: 28, delay: 2.4, duration: 15, opacity: 0.72 },
  { id: 27, emoji: '💐', anim: 'wiggle', x: 72, y: 55, size: 32, delay: 4.2, duration: 14, opacity: 0.74 },
  { id: 28, emoji: '😊', anim: 'bounce', x: 88, y: 60, size: 36, delay: 1.1, duration: 12, opacity: 0.62 },
  { id: 29, emoji: '🌷', anim: 'drift-c', x: 3, y: 72, size: 24, delay: 3.4, duration: 19, opacity: 0.75 },
  { id: 30, emoji: '✨', anim: 'twinkle', x: 20, y: 78, size: 18, delay: 0.2, duration: 9, opacity: 0.9 },
  { id: 31, emoji: '💗', anim: 'float-a', x: 38, y: 72, size: 34, delay: 2.1, duration: 17, opacity: 0.7 },
  { id: 32, emoji: '🌼', anim: 'drift-a', x: 52, y: 80, size: 26, delay: 4.8, duration: 18, opacity: 0.78 },
  { id: 33, emoji: '🎀', anim: 'wiggle', x: 66, y: 74, size: 28, delay: 1.3, duration: 13, opacity: 0.72 },
  { id: 34, emoji: '🌟', anim: 'twinkle', x: 80, y: 78, size: 22, delay: 3.6, duration: 11, opacity: 0.85 },
  { id: 35, emoji: '🦋', anim: 'float-b', x: 94, y: 72, size: 26, delay: 0.5, duration: 16, opacity: 0.74 },
  { id: 36, emoji: '💕', anim: 'drift-b', x: 10, y: 88, size: 28, delay: 2.9, duration: 20, opacity: 0.76 },
  { id: 37, emoji: '🌸', anim: 'float-c', x: 26, y: 92, size: 22, delay: 4.1, duration: 15, opacity: 0.7 },
  { id: 38, emoji: '☀️', anim: 'bounce', x: 44, y: 90, size: 30, delay: 1.7, duration: 14, opacity: 0.68 },
  { id: 39, emoji: '✨', anim: 'twinkle', x: 60, y: 88, size: 16, delay: 3, duration: 8, opacity: 0.92 },
  { id: 40, emoji: '🫶', anim: 'float-a', x: 74, y: 92, size: 30, delay: 0.8, duration: 17, opacity: 0.78 },
  { id: 41, emoji: '🌸', anim: 'drift-c', x: 34, y: 32, size: 20, delay: 5, duration: 21, opacity: 0.8 },
  { id: 42, emoji: '💖', anim: 'bounce', x: 68, y: 32, size: 22, delay: 2.3, duration: 13, opacity: 0.74 },
  { id: 43, emoji: '🎵', anim: 'wiggle', x: 82, y: 18, size: 24, delay: 4.4, duration: 12, opacity: 0.68 },
  { id: 44, emoji: '⭐', anim: 'twinkle', x: 14, y: 15, size: 16, delay: 1.9, duration: 10, opacity: 0.86 },
  { id: 45, emoji: '🌻', anim: 'float-b', x: 48, y: 68, size: 24, delay: 3.3, duration: 16, opacity: 0.72 },
  { id: 46, emoji: '💫', anim: 'twinkle', x: 86, y: 48, size: 18, delay: 0.1, duration: 9, opacity: 0.88 },
  { id: 47, emoji: '🪷', anim: 'drift-a', x: 2, y: 52, size: 26, delay: 2.7, duration: 19, opacity: 0.7 },
  { id: 48, emoji: '🧸', anim: 'float-c', x: 56, y: 14, size: 22, delay: 4.6, duration: 18, opacity: 0.66 },
]
</script>

<style scoped>
.dynamic-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.dynamic-bg.contained {
  position: absolute;
}

.bg-base {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    #fee8c8 0%,
    #f8f4ec 38%,
    #edf7f1 68%,
    #d4f1e0 100%
  );
  animation: baseGlow 18s ease-in-out infinite alternate;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  will-change: transform;
}

.blob-1 {
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, rgba(254, 220, 180, 0.48) 0%, transparent 70%);
  top: -12%;
  left: -6%;
  animation: driftWarm 24s ease-in-out infinite;
}

.blob-2 {
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(212, 241, 224, 0.5) 0%, transparent 70%);
  top: 20%;
  right: -8%;
  animation: driftCool 28s ease-in-out infinite;
}

.blob-3 {
  width: 380px;
  height: 380px;
  background: radial-gradient(circle, rgba(170, 205, 185, 0.38) 0%, transparent 70%);
  bottom: -8%;
  left: 30%;
  animation: driftMint 22s ease-in-out infinite;
}

.blob-4 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(228, 237, 229, 0.45) 0%, transparent 70%);
  bottom: 15%;
  right: 20%;
  animation: driftWarm 30s ease-in-out infinite reverse;
}

.emoji-layer {
  position: absolute;
  inset: 0;
  transition: opacity 0.4s ease;
}

.emoji-deco {
  position: absolute;
  display: block;
  line-height: 1;
  user-select: none;
  filter: drop-shadow(0 2px 6px rgba(255, 255, 255, 0.5));
  will-change: transform;
}

/* 大屏上背景 emoji 略微变淡，减少干扰 */
@media (min-width: 1200px) {
  .emoji-layer {
    opacity: 0.58;
  }

  .blob {
    opacity: 0.82;
  }
}

@media (min-width: 1600px) {
  .emoji-layer {
    opacity: 0.42;
  }

  .blob {
    opacity: 0.72;
  }

  .emoji-deco {
    filter: drop-shadow(0 1px 4px rgba(255, 255, 255, 0.35));
  }
}

.float-a { animation: floatA ease-in-out infinite; }
.float-b { animation: floatB ease-in-out infinite; }
.float-c { animation: floatC ease-in-out infinite; }
.drift-a { animation: driftA ease-in-out infinite; }
.drift-b { animation: driftB ease-in-out infinite; }
.drift-c { animation: driftC ease-in-out infinite; }
.bounce { animation: bounce ease-in-out infinite; }
.wiggle { animation: wiggle ease-in-out infinite; }
.twinkle { animation: twinkle ease-in-out infinite; }

@keyframes baseGlow {
  0% { filter: brightness(1) saturate(1); }
  100% { filter: brightness(1.03) saturate(1.08); }
}

@keyframes driftWarm {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(40px, 30px) scale(1.06); }
}

@keyframes driftCool {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-35px, 25px) scale(1.05); }
}

@keyframes driftMint {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -25px); }
}

@keyframes floatA {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(12px, -18px) rotate(8deg); }
}

@keyframes floatB {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(-14px, -22px) rotate(-10deg); }
}

@keyframes floatC {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33% { transform: translate(8px, -12px) rotate(5deg); }
  66% { transform: translate(-10px, -20px) rotate(-6deg); }
}

@keyframes driftA {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(20px, 10px) rotate(12deg); }
  75% { transform: translate(-15px, -12px) rotate(-8deg); }
}

@keyframes driftB {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(-18px, 15px) rotate(-15deg); }
}

@keyframes driftC {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  40% { transform: translate(16px, -14px) rotate(10deg); }
  80% { transform: translate(-12px, 8px) rotate(-5deg); }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-14px) scale(1.08); }
}

@keyframes wiggle {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(12deg); }
  75% { transform: rotate(-12deg); }
}

@keyframes twinkle {
  0%, 100% { transform: scale(1) rotate(0deg); opacity: inherit; }
  50% { transform: scale(1.35) rotate(20deg); }
}

@media (prefers-reduced-motion: reduce) {
  .blob, .bg-base, .emoji-deco {
    animation: none !important;
  }
}
</style>
