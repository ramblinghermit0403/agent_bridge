<template>
  <div class="carousel-container">
    <div class="card-content-wrapper">
      <transition name="card-swap" mode="out-in">
        <div class="carousel-card" :key="currentIndex">
          <div class="card-icon" v-html="currentCard.icon"></div>
          <h4 class="card-title">{{ currentCard.title }}</h4>
          <p class="card-description">{{ currentCard.description }}</p>
          <a :href="currentCard.link" target="_blank" class="card-link">Learn More →</a>
        </div>
      </transition>
    </div>

    <div class="carousel-navigation">
      <button @click="prevCard" class="nav-button" aria-label="Previous card"><</button>
      <div class="nav-dots">
        <span
          v-for="(card, index) in cards"
          :key="index"
          :class="{ active: index === currentIndex }"
          @click="goToCard(index)"
        ></span>
      </div>
      <button @click="nextCard" class="nav-button" aria-label="Next card">></button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';

// --- Card Content ---
const cards = [
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>`,
    title: 'Use Natural Language',
    description: "Orchestrate tools with simple prompts. Try asking: 'Summarize the latest report and email it to my team.'",
    link: '#'
  },
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"></path><path d="M12 5l7 7-7 7"></path></svg>`,
    title: 'Create Your Own Server',
    description: 'Connect custom tools by building a Model Context Server. Our open-source library makes it easy to start.',
    link: '#'
  },
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>`,
    title: 'Powered by Anthropic',
    description: 'Built on Anthropic\'s server library for robust, scalable, and secure tool integration. Discover the core tech.',
    link: '#'
  }
];

// --- Carousel Logic ---
const currentIndex = ref(0);
let autoPlayInterval = null;

const currentCard = computed(() => cards[currentIndex.value]);

const nextCard = () => {
  currentIndex.value = (currentIndex.value + 1) % cards.length;
  resetAutoPlay();
};

const prevCard = () => {
  currentIndex.value = (currentIndex.value - 1 + cards.length) % cards.length;
  resetAutoPlay();
};

const goToCard = (index) => {
  currentIndex.value = index;
  resetAutoPlay();
};

const startAutoPlay = () => {
  autoPlayInterval = setInterval(nextCard, 7000); // Change card every 7 seconds
};

const resetAutoPlay = () => {
  clearInterval(autoPlayInterval);
  startAutoPlay();
};

onMounted(() => {
  startAutoPlay();
});

onBeforeUnmount(() => {
  clearInterval(autoPlayInterval);
});
</script>

<style scoped>
.carousel-container {
  padding: 1rem 1rem;
  margin: 1rem;
  border-radius: 12px;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.card-content-wrapper {
  overflow: hidden;
  height: 140px; /* Fixed height for content to prevent layout shifts */
}

.carousel-card {
  text-align: center;
}

.card-icon {
  margin: 0 auto 0.75rem;
  color: var(--accent-color);
  width: 24px;
  height: 24px;
}

.card-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.card-description {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
}

.card-link {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--accent-color);
  text-decoration: none;
}
.card-link:hover {
  text-decoration: underline;
}

.carousel-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
}

.nav-button {
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.nav-button:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border-color: var(--text-secondary);
}

.nav-dots {
  display: flex;
  gap: 6px;
}
.nav-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--border-color);
  cursor: pointer;
  transition: background-color 0.2s;
}
.nav-dots span.active {
  background-color: var(--accent-color);
}

/* Card content transition */
.card-swap-enter-active,
.card-swap-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.card-swap-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.card-swap-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>