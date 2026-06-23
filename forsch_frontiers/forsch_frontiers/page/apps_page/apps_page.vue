<template>
  <div class="flex-1 min-h-0 overflow-auto bg-surface-gray-1">
    <div class="mx-auto max-w-4xl px-6 py-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-1">
        <h1 class="text-lg font-medium text-ink-gray-9">Apps</h1>
        <div class="flex items-center gap-4 text-xs text-ink-gray-5">
          <button
            @click="refreshAll"
            :disabled="refreshing"
            class="flex items-center gap-1 text-ink-gray-4 hover:text-ink-gray-7 disabled:opacity-50"
          >
            <LoaderIcon v-if="refreshing" class="size-3 animate-spin" />
            <RefreshCwIcon v-else class="size-3" />
            {{ refreshing ? 'Checking…' : 'Refresh' }}
          </button>
          <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-green-600" />live</span>
          <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-amber-500" />login</span>
          <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-gray-400" />unknown</span>
          <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-red-500" />down</span>
        </div>
      </div>
      <p v-if="lastRefresh" class="text-xs text-ink-gray-4 mb-5">
        Status checked {{ lastRefresh }}. Tailscale (100.120.21.13) links need the tailnet.
      </p>

      <!-- Loading -->
      <div v-if="loading" class="text-sm text-ink-gray-4 py-10 text-center">Loading apps…</div>

      <!-- Error -->
      <div v-else-if="error" class="text-sm text-red-500 py-10 text-center">{{ error }}</div>

      <!-- Groups -->
      <template v-else>
        <section v-for="group in groups" :key="group.name" class="mb-6">
          <h2 class="text-xs font-medium uppercase tracking-wide text-ink-gray-5 mb-2">{{ group.name }}</h2>
          <div class="grid gap-2.5" style="grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));">
            <div
              v-for="app in group.apps"
              :key="app.slug"
              class="relative flex items-center gap-3 rounded-lg border border-outline-gray-1 bg-surface-white px-3 py-2.5 transition-colors"
              :class="selectedApp === app.slug ? 'border-outline-gray-4 ring-1 ring-outline-gray-2' : 'hover:border-outline-gray-3'"
            >
              <!-- Status dot -->
              <span
                class="absolute top-2.5 right-2.5 size-2 rounded-full"
                :class="dotClass(app.status)"
                :title="app.status"
              />
              <!-- Icon -->
              <FeatherIcon :name="app.icon || 'box'" class="size-5 text-ink-gray-5 shrink-0" />
              <!-- Info -->
              <div class="min-w-0 flex-1">
                <a
                  :href="app.url"
                  target="_blank"
                  rel="noopener"
                  class="text-sm font-medium text-ink-gray-8 truncate block hover:text-ink-gray-9"
                >{{ app.app_name }}</a>
                <div class="text-xs text-ink-gray-4 truncate">{{ displayUrl(app.url) }}</div>
                <!-- Model selector -->
                <div class="mt-1 flex items-center gap-1.5">
                  <span class="text-[10px] text-ink-gray-4 uppercase tracking-wider shrink-0">model</span>
                  <select
                    :value="app.model_override || ''"
                    @change="setModel(app, $event.target.value)"
                    class="text-[11px] text-ink-gray-6 bg-surface-gray-1 border border-outline-gray-1 rounded px-1.5 py-0.5 truncate max-w-[160px] focus:outline-none focus:border-outline-gray-3"
                  >
                    <option value="">default</option>
                    <option v-for="m in availableModels" :key="m.id" :value="m.id">{{ m.id }}</option>
                  </select>
                  <span
                    v-if="app.model_override && modelSaving[app.slug]"
                    class="text-[10px] text-ink-gray-4"
                  >saving…</span>
                  <span
                    v-else-if="app.model_override && modelSaved[app.slug]"
                    class="text-[10px] text-green-600"
                  >✓</span>
                </div>
              </div>
              <!-- Actions -->
              <div class="flex items-center gap-1 shrink-0">
                <button
                  v-if="app.docker_container"
                  @click.stop="openLogs(app)"
                  class="p-1 rounded hover:bg-surface-gray-2 text-ink-gray-4 hover:text-ink-gray-7"
                  title="View logs"
                >
                  <FileTextIcon class="size-3.5" />
                </button>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- Log Drawer -->
      <Teleport to="body">
        <div
          v-if="logDrawer.open"
          class="fixed inset-0 z-50 flex justify-end"
          @keydown.esc="logDrawer.open = false"
        >
          <div class="absolute inset-0 bg-black/20" @click="logDrawer.open = false" />
          <div class="relative w-full max-w-2xl bg-surface-white shadow-xl flex flex-col">
            <div class="flex items-center justify-between px-4 py-3 border-b border-outline-gray-1">
              <div>
                <h3 class="text-sm font-medium text-ink-gray-9">{{ logDrawer.appName }}</h3>
                <p class="text-xs text-ink-gray-4">docker logs --tail {{ logDrawer.lines }}</p>
              </div>
              <button @click="logDrawer.open = false" class="p-1 rounded hover:bg-surface-gray-2">
                <XIcon class="size-4 text-ink-gray-5" />
              </button>
            </div>
            <div class="flex-1 overflow-auto p-4">
              <pre v-if="logDrawer.loading" class="text-xs text-ink-gray-4">Loading logs…</pre>
              <pre v-else-if="logDrawer.error" class="text-xs text-red-500">{{ logDrawer.error }}</pre>
              <pre v-else class="text-xs text-ink-gray-7 font-mono whitespace-pre-wrap break-all">{{ logDrawer.output }}</pre>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { FeatherIcon, FileTextIcon, RefreshCwIcon, XIcon, LoaderIcon } from 'lucide-vue-next'
import { createResource } from 'frappe-ui'

const loading = ref(true)
const error = ref(null)
const refreshing = ref(false)
const lastRefresh = ref(null)
const selectedApp = ref(null)
const apps = ref([])
const availableModels = ref([])
const modelSaving = ref({})
const modelSaved = ref({})

const logDrawer = ref({
  open: false,
  appName: '',
  slug: '',
  output: '',
  loading: false,
  error: null,
  lines: 100,
})

// Fetch all apps from DocType API
const appsResource = createResource({
  url: 'frappe.client.get_list',
  method: 'GET',
  params: {
    doctype: 'FF App Registry',
    filters: { enabled: 1 },
    fields: ['app_name', 'slug', 'group', 'icon', 'url', 'health_url',
             'docker_container', 'status', 'last_checked', 'model_override',
             'chainlit_port'],
    limit_page_length: 100,
    order_by: 'group asc, app_name asc',
  },
  onSuccess(data) {
    apps.value = data
    loading.value = false
  },
  onError(err) {
    error.value = err.message || 'Failed to load apps'
    loading.value = false
  },
})

// Fetch available models from LiteLLM
async function fetchModels() {
  try {
    const res = await fetch('/api/method/forsch_frontiers.api.app_ops.list_models', {
      credentials: 'include',
    })
    const data = await res.json()
    if (data.message) {
      availableModels.value = data.message
    }
  } catch (e) {
    console.error('Failed to load models:', e)
  }
}

// Set model override for an app
async function setModel(app, model) {
  const slug = app.slug
  modelSaving.value = { ...modelSaving.value, [slug]: true }
  modelSaved.value = { ...modelSaved.value, [slug]: false }

  try {
    const res = await fetch('/api/method/forsch_frontiers.api.app_ops.set_model', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug, model }),
    })
    const data = await res.json()
    if (data.message) {
      app.model_override = data.message.model_override
      modelSaved.value = { ...modelSaved.value, [slug]: true }
      setTimeout(() => {
        modelSaved.value = { ...modelSaved.value, [slug]: false }
      }, 2000)
    }
  } catch (e) {
    console.error('Failed to set model:', e)
  } finally {
    modelSaving.value = { ...modelSaving.value, [slug]: false }
  }
}

// Group apps by group field
const groups = computed(() => {
  const map = {}
  for (const app of apps.value) {
    const g = app.group || 'Other'
    if (!map[g]) map[g] = { name: g, apps: [] }
    map[g].apps.push(app)
  }
  return Object.values(map)
})

function dotClass(status) {
  if (status === 'live') return 'bg-green-600'
  if (status === 'login') return 'bg-amber-500'
  if (status === 'down') return 'bg-red-500'
  return 'bg-gray-400'
}

function displayUrl(url) {
  return url ? url.replace(/^https?:\/\//, '') : ''
}

async function openLogs(app) {
  logDrawer.value = {
    open: true,
    appName: app.app_name,
    slug: app.slug,
    output: '',
    loading: true,
    error: null,
    lines: 100,
  }

  try {
    const res = await fetch(
      `/api/method/forsch_frontiers.api.app_ops.logs?slug=${app.slug}&lines=100`,
      { credentials: 'include' }
    )
    const data = await res.json()
    if (data.message) {
      logDrawer.value.output = data.message.output || '(empty)'
    } else {
      logDrawer.value.error = data.exc_type || 'Unknown error'
    }
  } catch (e) {
    logDrawer.value.error = e.message
  } finally {
    logDrawer.value.loading = false
  }
}

async function refreshAll() {
  refreshing.value = true
  try {
    const res = await fetch('/api/method/forsch_frontiers.api.app_ops.status_all', {
      credentials: 'include',
    })
    const data = await res.json()
    if (data.message) {
      for (const status of data.message) {
        const app = apps.value.find(a => a.slug === status.slug)
        if (app) {
          app.status = status.status
          app.last_checked = status.last_checked
        }
      }
      lastRefresh.value = new Date().toLocaleTimeString()
    }
  } catch (e) {
    console.error('Status refresh failed:', e)
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  appsResource.fetch()
  fetchModels()
})
</script>
