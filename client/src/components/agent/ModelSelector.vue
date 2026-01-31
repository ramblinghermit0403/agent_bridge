<template>
  <div class="relative inline-block text-left" ref="container">
    <button 
      type="button" 
      class="selector-trigger" 
      :class="{ 'is-open': isOpen }"
      @click="toggleDropdown"
      :disabled="disabled"
    >
      <span class="font-medium">{{ selectedModel?.name || 'Select Model' }}</span>
      <svg class="chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    </button>

    <div v-if="isOpen" class="dropdown-menu" :style="dropdownStyle">
      <div class="py-1">
        <button
          v-for="model in structuredModels"
          :key="model.id"
          class="menu-item"
          :class="{ 'selected': isSelected(model) }"
          @click="selectModel(model)"
        >
          <div class="flex justify-between items-start w-full">
            <div class="flex flex-col items-start text-left">
              <span class="item-name">{{ model.displayName }}</span>
              <span class="item-desc">{{ model.description }}</span>
            </div>
            <div class="flex items-center gap-2">
                <span v-if="model.badge" class="badge-upgrade">{{ model.badge }}</span>
                <svg v-if="isSelected(model)" class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
            </div>
          </div>
        </button>
      </div>

      <div class="border-t border-gray-100 mt-1 pt-1">
        <button class="menu-item more-models-btn" @click="emitMore">
          <span>More models</span>
          <svg class="w-4 h-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModelSelector',
  props: {
    modelValue: {
      type: Object,
      default: null
    },
    options: {
      type: Array,
      default: () => []
    },
    disabled: {
        type: Boolean,
        default: false
    },
    placement: {
        type: String,
        default: 'top'
    }
  },
  emits: ['update:modelValue', 'more-clicked'],
  data() {
    return {
      isOpen: false
    }
  },
  computed: {
    selectedModel() {
      if (!this.modelValue) return null;
      const structured = this.structuredModels.find(m => m.id === this.modelValue.id);
      return structured || this.modelValue;
    },
    structuredModels() {
      return this.options.map(opt => {
        const nameLower = opt.name.toLowerCase();
        let displayName = opt.name;
        let description = "Capable and efficient model";
        let badge = null;

        if (nameLower.includes('opus')) {
            displayName = opt.name.replace(/claude\s*3\.?/i, '').trim();
            description = "Most capable for complex work";
            badge = "Upgrade";
        } else if (nameLower.includes('sonnet')) {
             displayName = opt.name.replace(/claude\s*3\.?/i, '').trim();
             description = "Best for everyday tasks";
        } else if (nameLower.includes('haiku')) {
             displayName = opt.name.replace(/claude\s*3\.?/i, '').trim();
             description = "Fastest for quick answers";
        } else if (nameLower.includes('flash')) {
            description = "Fast and low latency";
        } else if (nameLower.includes('pro')) {
            description = "High performance model";
        }

        return {
          ...opt,
          displayName,
          description,
          badge
        };
      });
    },
    dropdownStyle() {
      if (this.placement === 'top') {
        return { bottom: '120%', top: 'auto', transformOrigin: 'bottom left' };
      } else {
        return { top: '120%', bottom: 'auto', transformOrigin: 'top left' };
      }
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    toggleDropdown() {
      if (!this.disabled) {
        this.isOpen = !this.isOpen;
      }
    },
    selectModel(model) {
      this.$emit('update:modelValue', model);
      this.isOpen = false;
    },
    emitMore() {
        this.$emit('more-clicked');
        this.isOpen = false;
    },
    handleClickOutside(event) {
      if (this.$refs.container && !this.$refs.container.contains(event.target)) {
        this.isOpen = false;
      }
    },
    isSelected(model) {
      return this.modelValue && this.modelValue.id === model.id;
    }
  }
}
</script>

<style scoped>
.relative { position: relative; }
.inline-block { display: inline-block; }
.text-left { text-align: left; }

.selector-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  background-color: var(--bg-secondary);
  border: 1px solid transparent; 
  border-radius: 0.5rem;
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  height: 34px;  
}

.selector-trigger:hover {
  background-color: var(--bg-primary); 
}

.selector-trigger.is-open {
  background-color: var(--bg-primary); 
}

.selector-trigger:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.chevron {
  width: 1.25rem;
  height: 1.25rem;
  color: var(--text-secondary);
  transition: transform 0.2s;
}

.is-open .chevron {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  left: 0;
  width: 220px;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  z-index: 50;
  overflow: hidden;
  animation: scaleIn 0.1s ease-out;
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.menu-item {
  width: 100%;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: background-color 0.15s;
  background: transparent;
  border: none;
  display: block;
}

.menu-item:hover {
  background-color: var(--bg-secondary);
}

.item-name {
  display: block;
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.9rem;
  margin-bottom: 0px;
}

.item-desc {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 400;
  line-height: 1.25;
}

.badge-upgrade {
  font-size: 0.7rem;
  font-weight: 600;
  color: #2563eb; /* Blue */
  background-color: #eff6ff;
  border: 1px solid #dbeafe;
  padding: 0.1rem 0.5rem;
  border-radius: 9999px;
  white-space: nowrap;
}

.checkmark {
  width: 1.25rem;
  height: 1.25rem;
  color: #2563eb;
}

.more-models-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-primary);
  font-weight: 500;
}

.more-models-btn:hover {
    background-color: var(--bg-secondary);
}

@media (prefers-color-scheme: dark) {
  .badge-upgrade {
    background-color: rgba(37, 99, 235, 0.1);
    border-color: rgba(37, 99, 235, 0.2);
    color: #60a5fa;
  }
}
</style>
