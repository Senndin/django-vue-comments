<script setup>
/** Панель кнопок розмітки: обгортає виділений текст дозволеним тегом (R23). */
const props = defineProps({
  // Посилання на `<textarea>`: щоб вставити теги саме довкола виділення.
  textarea: { type: Object, default: null },
  modelValue: { type: String, required: true },
})

const emit = defineEmits(['update:modelValue'])

const tags = [
  { name: 'i', label: '[i]', title: 'Italic' },
  { name: 'strong', label: '[strong]', title: 'Bold' },
  { name: 'code', label: '[code]', title: 'Code' },
  { name: 'a', label: '[a]', title: 'Link' },
]

function buildTag(name) {
  // У посилання обов'язковий href, тож одразу даємо заготовку з правильною схемою (R19).
  return name === 'a'
    ? { open: '<a href="https://" title="">', close: '</a>' }
    : { open: `<${name}>`, close: `</${name}>` }
}

function wrap(name) {
  const field = props.textarea
  const { open, close } = buildTag(name)
  const start = field?.selectionStart ?? props.modelValue.length
  const end = field?.selectionEnd ?? props.modelValue.length
  const selected = props.modelValue.slice(start, end)

  const text =
    props.modelValue.slice(0, start) + open + selected + close + props.modelValue.slice(end)
  emit('update:modelValue', text)

  // Повертаємо фокус і ставимо курсор усередину тегів — можна одразу писати далі.
  if (field) {
    field.focus()
    const caret = start + open.length + selected.length
    requestAnimationFrame(() => field.setSelectionRange(start + open.length, caret))
  }
}
</script>

<template>
  <div class="toolbar" role="group" aria-label="Formatting">
    <button
      v-for="tag in tags"
      :key="tag.name"
      type="button"
      :title="tag.title"
      @click="wrap(tag.name)"
    >
      {{ tag.label }}
    </button>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 0.35rem;
  margin-bottom: 0.35rem;
}

button {
  padding: 0.2rem 0.55rem;
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
}
</style>
