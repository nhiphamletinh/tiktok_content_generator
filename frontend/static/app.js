const analyzeBtn = document.getElementById('analyzeBtn')
const recsBtn = document.getElementById('recsBtn')
const urlInput = document.getElementById('urlInput')

const screenStart = document.getElementById('screen-start')
const screenClusters = document.getElementById('screen-clusters')
const screenRecs = document.getElementById('screen-recs')

const processingView = document.getElementById('processingView')
const clustersView = document.getElementById('clustersView')
const clustersDiv = document.getElementById('clusters')

const recsProcessing = document.getElementById('recsProcessing')
const recsView = document.getElementById('recsView')
const insightsDiv = document.getElementById('insights')
const overlay = document.getElementById('overlay')
const againBtn = document.getElementById('againBtn')

function showScreen(id){
  [screenStart, screenClusters, screenRecs].forEach(s => s.classList.remove('active'))
  document.getElementById(id).classList.add('active')
}

analyzeBtn.addEventListener('click', async () => {
  // For MVP the URL is ignored — kept for UI purposes
  showScreen('screen-clusters')
  processingView.style.display = 'flex'
  clustersView.style.display = 'none'
  clustersDiv.innerHTML = ''
  analyzeBtn.disabled = true

  try {
    const resp = await fetch('/analyze', { method: 'POST' })
    const data = await resp.json()
    if (!data.ok) throw new Error(data.error || 'Analyze failed')
    renderClusters(data.clusters)
    processingView.style.display = 'none'
    clustersView.style.display = 'block'
  } catch (e) {
    processingView.style.display = 'none'
    clustersView.style.display = 'block'
    clustersDiv.innerHTML = `<div style="color:#ffb4b4">Error: ${e.message}</div>`
  } finally {
    analyzeBtn.disabled = false
  }
})

recsBtn.addEventListener('click', async () => {
  showScreen('screen-recs')
  recsProcessing.style.display = 'flex'
  recsView.style.display = 'none'
  insightsDiv.innerHTML = ''
  recsBtn.disabled = true

  try {
    const resp = await fetch('/recommend', { method: 'POST' })
    const data = await resp.json()
    if (!data.ok) throw new Error(data.error || 'Recommend failed')
    renderInsights(data.insights)
    recsProcessing.style.display = 'none'
    recsView.style.display = 'block'
  } catch (e) {
    recsProcessing.style.display = 'none'
    recsView.style.display = 'block'
    insightsDiv.innerHTML = `<div style="color:#ffb4b4">Error: ${e.message}</div>`
  } finally {
    recsBtn.disabled = false
  }
})

function renderClusters(clusters){
  clustersDiv.innerHTML = ''
  // clusters could be an array or object; normalize
  const items = Array.isArray(clusters) ? clusters : Object.values(clusters)
  items.forEach(c => {
    // cloud element with title only; on click expand to show examples
    const div = document.createElement('div')
    div.className = 'cloud'
    const title = document.createElement('div')
    title.className = 'title'
    const clusterTitle = c.name || c.cluster_title || (`Cluster ${c.cluster_id ?? c.id}`)
    title.textContent = `${clusterTitle}`
    div.appendChild(title)

    const examples = document.createElement('div')
    examples.className = 'examples'
    const reps = c.representative_comments || c.examples || []
    if (reps.length === 0) {
      examples.innerHTML = '<div class="small">No example comments</div>'
    } else {
      reps.slice(0,6).forEach(rc => {
        const p = document.createElement('div')
        p.textContent = rc.text ?? rc
        p.style.padding = '6px 0'
        p.style.borderBottom = '1px solid rgba(255,255,255,0.03)'
        examples.appendChild(p)
      })
    }
    div.appendChild(examples)


    // open modal showing cluster details when clicked
    div.addEventListener('click', (e) => {
      e.stopPropagation()
      openClusterModal(c)
    })


    clustersDiv.appendChild(div)
  })
}

function renderInsights(insights){
  insightsDiv.innerHTML = ''
  insights.forEach(item => {
    const out = document.createElement('div')
    out.className = 'insight'
    const title = document.createElement('div')
    title.innerHTML = `<strong>${item.cluster_title || 'Cluster ' + item.cluster_id}</strong> <span style='color:var(--muted);margin-left:8px'>score: ${('demand_score' in item)? item.demand_score : ''}</span>`
    out.appendChild(title)
    if (item.pain_point){
      const pain = document.createElement('div')
      pain.textContent = item.pain_point
      pain.className = 'small'
      out.appendChild(pain)
    }
    const hook = document.createElement('div')
    hook.innerHTML = `<strong>Hook:</strong> ${item.video_outline?.hook ?? ''}`
    out.appendChild(hook)
    const body = document.createElement('div')
    body.innerHTML = `<strong>Body:</strong> ${item.video_outline?.body ?? ''}`
    out.appendChild(body)
    const cta = document.createElement('div')
    cta.innerHTML = `<strong>CTA:</strong> ${item.video_outline?.cta ?? ''}`
    out.appendChild(cta)
    insightsDiv.appendChild(out)
  })
}

function openClusterModal(cluster){
  // create modal container
  collapseAllExpanded()
  const modal = document.createElement('div')
  modal.className = 'cluster-modal'

  const closeBtn = document.createElement('button')
  closeBtn.className = 'close'
  closeBtn.textContent = '✕'
  closeBtn.addEventListener('click', () => closeClusterModal(modal))
  modal.appendChild(closeBtn)

  const title = document.createElement('div')
  title.className = 'title'
  title.textContent = cluster.cluster_title || (`Cluster ${cluster.cluster_id ?? cluster.id}`)
  modal.appendChild(title)
  // subtitle
  const subtitle = document.createElement('div')
  subtitle.className = 'subtitle'
  subtitle.textContent = 'These are some example comments:'
  modal.appendChild(subtitle)

  const examples = document.createElement('div')
  examples.className = 'examples'
  const reps = cluster.representative_comments || cluster.examples || []
  if (!reps || reps.length === 0){
    const p = document.createElement('div')
    p.textContent = 'No example comments'
    examples.appendChild(p)
  } else {
    reps.forEach(rc => {
      const p = document.createElement('div')
      p.textContent = rc.text ?? rc
      p.style.color = '#081219'
      examples.appendChild(p)
    })
  }
  modal.appendChild(examples)

  document.body.appendChild(modal)
  overlay.style.display = 'block'
  document.body.style.overflow = 'hidden'
}

function closeClusterModal(modal){
  if (modal && modal.remove) modal.remove()
  overlay.style.display = 'none'
  document.body.style.overflow = ''
}

function collapseAllExpanded(){
  // remove any modal
  const m = document.querySelector('.cluster-modal')
  if (m) m.remove()
  overlay.style.display = 'none'
  document.body.style.overflow = ''
}

// overlay click collapses
overlay?.addEventListener('click', () => collapseAllExpanded())

// ESC closes
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') collapseAllExpanded() })

// Analyze another video (reset to start)
againBtn?.addEventListener('click', () => {
  collapseAllExpanded()
  insightsDiv.innerHTML = ''
  showScreen('screen-start')
})

