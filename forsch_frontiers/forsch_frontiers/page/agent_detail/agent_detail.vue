<template>
  <div class="flex-1 min-h-0 overflow-auto bg-surface-gray-1">
    <div class="mx-auto max-w-3xl px-6 py-6">

      <!-- Breadcrumb -->
      <nav class="flex items-center gap-2 text-xs text-ink-gray-5 mb-5">
        <a
          href="#"
          class="hover:text-ink-gray-8 underline underline-offset-2"
          @click.prevent="handleBackToProject"
        >
          ← Back to Project
        </a>
        <span class="text-ink-gray-3">/</span>
        <span class="text-ink-gray-6 font-medium">Project: {{ mockProject }}</span>
        <span class="text-ink-gray-3">/</span>
        <span class="text-ink-gray-8 font-medium">{{ mockAgent.name }}</span>
      </nav>

      <!-- Header row: Name + Status pill -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <h1 class="text-lg font-medium text-ink-gray-9">{{ mockAgent.name }}</h1>
          <span
            class="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
            :class="statusClass(mockAgent.status)"
          >
            <span class="size-2 rounded-full" :class="statusDotClass(mockAgent.status)" />
            {{ statusLabel(mockAgent.status) }}
          </span>
        </div>
      </div>

      <!-- Config form -->
      <div class="space-y-5">

        <!-- Name (read-only) -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">Name</label>
          <input
            type="text"
            :value="mockAgent.name"
            disabled
            class="w-full text-sm text-ink-gray-7 bg-surface-gray-2 border border-outline-gray-1 rounded-lg px-3 py-2 cursor-not-allowed opacity-60"
          />
          <p class="text-[11px] text-ink-gray-4 mt-1">Unique within cluster. Lowercase + underscores.</p>
        </div>

        <!-- Model dropdown -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">Model</label>
          <select
            v-model="mockAgent.model"
            class="w-full text-sm text-ink-gray-8 bg-surface-white border border-outline-gray-1 rounded-lg px-3 py-2 focus:outline-none focus:border-outline-gray-4 focus:ring-1 focus:ring-outline-gray-2"
          >
            <option v-for="m in mockModels" :key="m" :value="m">{{ m }}</option>
          </select>
          <!-- TODO: Task 6 — populate from /api/method/forsch_frontiers.api.agent_config.list_models -->
        </div>

        <!-- Temperature slider with labeled zones -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">
            Temperature
            <span class="ml-2 text-ink-gray-7 font-semibold">{{ mockAgent.temperature.toFixed(1) }}</span>
            <span class="ml-1 text-ink-gray-4 font-normal normal-case">— {{ tempZone(mockAgent.temperature) }}</span>
          </label>
          <div class="relative">
            <!-- Zone bar behind slider -->
            <div class="flex h-1.5 rounded-full overflow-hidden mb-3">
              <div class="bg-blue-400 flex-none" style="width: 25%"></div>
              <div class="bg-green-400 flex-none" style="width: 37.5%"></div>
              <div class="bg-orange-400 flex-none" style="width: 37.5%"></div>
            </div>
            <input
              type="range"
              v-model.number="mockAgent.temperature"
              min="0"
              max="1"
              step="0.05"
              class="w-full h-2 appearance-none bg-transparent cursor-pointer accent-blue-500 relative z-10 -mt-4"
            />
            <!-- Zone labels -->
            <div class="flex justify-between text-[10px] text-ink-gray-4 mt-1 px-0.5">
              <span>Precise</span>
              <span>Balanced</span>
              <span>Creative</span>
            </div>
          </div>
          <!-- TODO: Task 6 — wire to generate_config.temperature -->
        </div>

        <!-- Max Tokens -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">
            Max Tokens
            <span class="ml-1 text-ink-gray-4 font-normal normal-case">(max_output_tokens)</span>
          </label>
          <input
            type="number"
            v-model.number="mockAgent.maxTokens"
            min="1"
            max="8192"
            class="w-40 text-sm text-ink-gray-8 bg-surface-white border border-outline-gray-1 rounded-lg px-3 py-2 focus:outline-none focus:border-outline-gray-4 focus:ring-1 focus:ring-outline-gray-2"
          />
          <p class="text-[11px] text-ink-gray-4 mt-1">Maximum tokens the model can generate. Default 500.</p>
          <!-- TODO: Task 6 — wire to generate_config.max_output_tokens -->
        </div>

        <!-- Advanced section (collapsed by default) -->
        <details class="group">
          <summary
            class="flex items-center gap-2 text-xs font-medium text-ink-gray-5 uppercase tracking-wider cursor-pointer select-none hover:text-ink-gray-7"
          >
            <svg class="size-3 text-ink-gray-4 group-open:rotate-90 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
            Advanced
          </summary>
          <div class="mt-3 pl-5 border-l-2 border-outline-gray-1 space-y-4">
            <!-- Top-p -->
            <div>
              <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">
                Top-p
                <span class="ml-1 text-ink-gray-4 font-normal normal-case">(nucleus sampling)</span>
              </label>
              <input
                type="number"
                v-model.number="mockAgent.topP"
                min="0"
                max="1"
                step="0.05"
                class="w-32 text-sm text-ink-gray-8 bg-surface-white border border-outline-gray-1 rounded-lg px-3 py-2 focus:outline-none focus:border-outline-gray-4 focus:ring-1 focus:ring-outline-gray-2"
              />
              <p class="text-[11px] text-ink-gray-4 mt-1">Tokens selected until cumulative probability reaches this value. Default 0.95.</p>
              <!-- TODO: Task 6 — wire to generate_config.top_p -->
            </div>
          </div>
        </details>

        <!-- System Instruction -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">System Instruction</label>
          <textarea
            v-model="mockAgent.instruction"
            rows="5"
            class="w-full text-sm text-ink-gray-8 bg-surface-white border border-outline-gray-1 rounded-lg px-3 py-2.5 focus:outline-none focus:border-outline-gray-4 focus:ring-1 focus:ring-outline-gray-2 resize-y min-h-[100px]"
            placeholder="You are a helpful assistant..."
          />
          <p class="text-[11px] text-ink-gray-4 mt-1">Dynamic system instruction. Supports placeholder processing.</p>
          <!-- TODO: Task 6 — wire to generate_config.system_instruction -->
        </div>

        <!-- Tools -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">
            Tools
            <span class="ml-1 text-ink-gray-4 font-normal normal-case">
              ({{ mockAgent.tools.length }} / 7 slots used)
            </span>
          </label>

          <!-- Warning at 5 tools -->
          <div
            v-if="mockAgent.tools.length >= 5 && mockAgent.tools.length < 7"
            class="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-2"
          >
            <svg class="size-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            5 of 7 tool slots used (soft cap). Consider splitting into a sub-agent.
          </div>

          <!-- Block at 7 tools -->
          <div
            v-if="mockAgent.tools.length >= 7"
            class="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-2"
          >
            <svg class="size-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            7+ tools degrades reliability. Consider splitting into a sub-agent.
          </div>

          <!-- Tool chips -->
          <div class="flex flex-wrap gap-2 mb-3">
            <span
              v-for="(tool, idx) in mockAgent.tools"
              :key="tool.name"
              class="inline-flex items-center gap-1.5 text-xs font-medium bg-surface-white border border-outline-gray-2 text-ink-gray-7 rounded-full pl-3 pr-1.5 py-1"
            >
              <svg class="size-3 text-green-500 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span class="truncate max-w-[180px]">{{ tool.name }}</span>
              <button
                @click="removeTool(idx)"
                class="size-5 flex items-center justify-center rounded-full hover:bg-surface-gray-2 text-ink-gray-4 hover:text-ink-gray-7 transition-colors"
                title="Remove tool"
              >
                <svg class="size-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </span>
          </div>

          <!-- Add Tool button -->
          <button
            @click="showToolPicker = !showToolPicker"
            class="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-800 border border-outline-gray-2 hover:border-blue-300 rounded-full px-3 py-1.5 transition-colors"
          >
            <svg class="size-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Add Tool
          </button>

          <!-- Tool picker (ADK components from list_tools endpoint) -->
          <div
            v-if="showToolPicker"
            class="mt-3 border border-outline-gray-1 rounded-lg bg-surface-white overflow-hidden"
          >
            <div class="px-3 py-2 border-b border-outline-gray-1 bg-surface-gray-1">
              <input
                v-model="toolSearch"
                type="text"
                placeholder="Search tools..."
                class="w-full text-xs text-ink-gray-8 bg-transparent focus:outline-none placeholder:text-ink-gray-4"
              />
            </div>
            <div class="max-h-48 overflow-y-auto">
              <button
                v-for="tool in filteredAvailableTools"
                :key="tool.name"
                @click="addTool(tool)"
                class="w-full text-left px-3 py-2 text-xs hover:bg-surface-gray-1 border-b border-outline-gray-5 last:border-b-0 transition-colors"
              >
                <div class="font-medium text-ink-gray-8">{{ tool.name }}</div>
                <div class="text-ink-gray-4 mt-0.5">{{ tool.description }}</div>
                <div class="flex items-center gap-2 mt-1">
                  <span
                    class="text-[10px] px-1.5 py-0.5 rounded"
                    :class="riskClass(tool.risk_level)"
                  >
                    {{ tool.risk_level }}
                  </span>
                  <span class="text-[10px] text-ink-gray-4">{{ tool.source }}</span>
                </div>
              </button>
              <div
                v-if="filteredAvailableTools.length === 0"
                class="px-3 py-4 text-xs text-ink-gray-4 text-center"
              >
                No tools found matching "{{ toolSearch }}"
              </div>
            </div>
          </div>
          <!-- TODO: Task 6 — replace mockAvailableTools with GET /api/method/forsch_frontiers.api.agent_tools.list -->
        </div>

        <!-- Sub-Agents (read-only) -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">Sub-Agents</label>
          <p class="text-sm text-ink-gray-4 italic">none wired</p>
          <!-- TODO: Phase 2 — editable sub-agent wiring -->
        </div>

        <!-- Parent (read-only) -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-5 uppercase tracking-wider mb-1.5">Parent</label>
          <p class="text-sm text-ink-gray-7">{{ mockAgent.parent || '—' }}</p>
        </div>

      </div>

      <!-- Action buttons -->
      <div class="flex items-center gap-3 mt-8 pt-5 border-t border-outline-gray-1">
        <!-- Save button (disabled when clean) -->
        <button
          :disabled="!isDirty"
          class="inline-flex items-center gap-1.5 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          :class="isDirty
            ? 'bg-ink-gray-9 text-surface-white hover:bg-ink-gray-8'
            : 'bg-surface-gray-2 text-ink-gray-4 cursor-not-allowed'"
        >
          <svg class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
          </svg>
          Save
        </button>
        <!-- TODO: Task 6 — wire Save to POST /api/method/forsch_frontiers.api.agent_config.save -->

        <!-- Generate & Verify -->
        <button
          class="inline-flex items-center gap-1.5 text-sm font-medium px-4 py-2 rounded-lg bg-blue-600 text-surface-white hover:bg-blue-700 transition-colors"
        >
          <svg class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          Generate &amp; Verify
        </button>
        <!-- TODO: Task 6 — wire to POST /api/method/forsch_frontiers.api.agent_factory.generate -->

        <!-- Delete (collapsed) -->
        <details class="relative ml-auto">
          <summary class="text-xs text-ink-gray-4 hover:text-red-500 cursor-pointer select-none transition-colors">
            Delete Agent
          </summary>
          <div class="absolute right-0 top-8 z-10 bg-surface-white border border-red-200 rounded-lg shadow-lg p-4 w-64">
            <p class="text-xs text-ink-gray-7 font-medium mb-2">Confirm deletion?</p>
            <p class="text-xs text-ink-gray-4 mb-3">This will permanently remove the agent config. This cannot be undone.</p>
            <div class="flex gap-2">
              <button class="text-xs font-medium px-3 py-1.5 rounded bg-red-600 text-surface-white hover:bg-red-700">
                Delete
              </button>
              <button class="text-xs font-medium px-3 py-1.5 rounded bg-surface-gray-2 text-ink-gray-6 hover:bg-surface-gray-3">
                Cancel
              </button>
            </div>
          </div>
        </details>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// ── Mock data (Phase 1 — static UI, no data binding) ──────────────────────
// TODO: Task 6 — replace with GET /api/method/forsch_frontiers.api.agent_config.get

const mockProject = ref('demo')

const mockAgent = ref({
  name: 'calendar_specialist',
  model: 'gemini-2.5-flash',
  temperature: 0.3,
  maxTokens: 500,
  topP: 0.95,
  instruction:
    'You manage the family calendar. You are strictly logical. Always confirm before booking.',
  tools: [
    { name: 'check_schedule', description: 'Check calendar for events on a specific date' },
    { name: 'book_event', description: 'Create calendar event' },
  ],
  parent: 'primary_assistant',
  status: 'built',
})

// Mock available models (populated from LiteLLM /models endpoint in production)
const mockModels = ref([
  'gemini-2.5-flash',
  'gemini-2.5-pro',
  'gpt-5.5',
  'glm-5.2',
  'deepseek-v4-pro',
  'claude-sonnet-4',
  'gemini-3.5-flash',
])

// Mock available tools — ADK components from list_tools endpoint (NOT agent_tools.yaml)
// TODO: Task 6 — replace with GET /api/method/forsch_frontiers.api.agent_tools.list
const mockAvailableTools = ref([
  { name: 'check_schedule', description: 'Check calendar for events on a specific date', source: 'google_calendar', risk_level: 'low' },
  { name: 'book_event', description: 'Create calendar event', source: 'google_calendar', risk_level: 'medium' },
  { name: 'get_crm_health_snapshot', description: 'Fetch CRM health status snapshot', source: 'crm_api', risk_level: 'low' },
  { name: 'list_recent_crm_leads', description: 'List recent CRM leads', source: 'crm_api', risk_level: 'low' },
  { name: 'send_email', description: 'Send an email via SMTP', source: 'email', risk_level: 'high' },
  { name: 'search_web', description: 'Search the web via configured search engine', source: 'web_search', risk_level: 'low' },
  { name: 'run_python', description: 'Execute Python code in sandboxed environment', source: 'code_executor', risk_level: 'high' },
  { name: 'read_file', description: 'Read contents of a file from workspace', source: 'filesystem', risk_level: 'medium' },
  { name: 'write_file', description: 'Write contents to a file in workspace', source: 'filesystem', risk_level: 'medium' },
  { name: 'query_database', description: 'Execute SQL query against configured database', source: 'database', risk_level: 'medium' },
])

// ── Tool picker ────────────────────────────────────────────────────────────

const showToolPicker = ref(false)
const toolSearch = ref('')

const filteredAvailableTools = computed(() => {
  const query = toolSearch.value.toLowerCase()
  const assignedNames = new Set(mockAgent.value.tools.map((t) => t.name))
  return mockAvailableTools.value.filter(
    (t) => !assignedNames.has(t.name) && (
      !query ||
      t.name.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query)
    )
  )
})

function addTool(tool) {
  if (mockAgent.value.tools.length >= 7) return
  mockAgent.value.tools.push({ name: tool.name, description: tool.description })
  toolSearch.value = ''
  showToolPicker.value = false
}

function removeTool(idx) {
  mockAgent.value.tools.splice(idx, 1)
}

// ── Dirty tracking ─────────────────────────────────────────────────────────
// TODO: Task 6 — compare against saved config from GET endpoint

const savedSnapshot = ref(JSON.stringify(mockAgent.value))
const isDirty = computed(() => {
  return JSON.stringify(mockAgent.value) !== savedSnapshot.value
})

// ── Helpers ────────────────────────────────────────────────────────────────

function tempZone(temp) {
  if (temp <= 0.2) return 'Precise'
  if (temp <= 0.6) return 'Balanced'
  return 'Creative'
}

function riskClass(level) {
  if (level === 'low') return 'bg-green-50 text-green-700'
  if (level === 'medium') return 'bg-amber-50 text-amber-700'
  return 'bg-red-50 text-red-700'
}

// ── Status pill helpers ────────────────────────────────────────────────────

function statusClass(status) {
  switch (status) {
    case 'blank':   return 'bg-surface-gray-2 text-ink-gray-5'
    case 'building': return 'bg-amber-50 text-amber-700'
    case 'built':   return 'bg-green-50 text-green-700'
    case 'error':   return 'bg-red-50 text-red-700'
    default:        return 'bg-surface-gray-2 text-ink-gray-5'
  }
}

function statusDotClass(status) {
  switch (status) {
    case 'blank':   return 'bg-ink-gray-4'
    case 'building': return 'bg-amber-500'
    case 'built':   return 'bg-green-600'
    case 'error':   return 'bg-red-500'
    default:        return 'bg-ink-gray-4'
  }
}

function statusLabel(status) {
  switch (status) {
    case 'blank':   return 'blank'
    case 'building': return 'building'
    case 'built':   return 'built'
    case 'error':   return 'error'
    default:        return status || 'blank'
  }
}

// ── Navigation ─────────────────────────────────────────────────────────────

function handleBackToProject() {
  // TODO: Task 6 — navigate back to project view (route change)
  console.log('Back to project:', mockProject.value)
}
</script>
