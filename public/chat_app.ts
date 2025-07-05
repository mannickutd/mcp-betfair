import { marked } from 'https://cdnjs.cloudflare.com/ajax/libs/marked/15.0.0/lib/marked.esm.js'

const convElement = document.getElementById('conversation')
const promptInput = document.getElementById('prompt-input') as HTMLInputElement
const spinner = document.getElementById('spinner')

// Retrieve the username from the URL query parameters
const urlParams = new URLSearchParams(window.location.search)
const username = urlParams.get('username');
const sessionId = urlParams.get('session_id');

if (!username || !sessionId) {
  console.error('Username and session ID are required to use the chat.');
  alert('Missing username or session ID. Please go back to the start page.');
  window.location.href = '/start/';
}

// Stream the response and render messages as each chunk is received
async function onFetchResponse(response: Response): Promise<void> {
  let text = ''
  let decoder = new TextDecoder()
  if (response.ok) {
    const reader = response.body.getReader()
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }
      text += decoder.decode(value)
      addMessages(text)
      spinner.classList.remove('active')
    }
    addMessages(text)
    promptInput.disabled = false
    promptInput.focus()
  } else {
    const text = await response.text()
    console.error(`Unexpected response: ${response.status}`, { response, text })
    throw new Error(`Unexpected response: ${response.status}`)
  }
}

// The format of messages
interface Message {
  role: string
  content: string
  timestamp: string
}

// Render messages into the `#conversation` element
function addMessages(responseText: string) {
  const lines = responseText.split('\n')
  const messages: Message[] = lines.filter(line => line.length > 1).map(j => JSON.parse(j))
  for (const message of messages) {
    const { timestamp, role, content } = message
    const id = `msg-${timestamp}`
    let msgDiv = document.getElementById(id)
    if (!msgDiv) {
      msgDiv = document.createElement('div')
      msgDiv.id = id
      msgDiv.title = `${role} at ${timestamp}`
      msgDiv.classList.add('border-top', 'pt-2', role)
      convElement.appendChild(msgDiv)
    }
    msgDiv.innerHTML = marked.parse(content)
  }
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

function onError(error: any) {
  console.error(error)
  document.getElementById('error').classList.remove('d-none')
  document.getElementById('spinner').classList.remove('active')
}

// Handle form submission
async function onSubmit(e: SubmitEvent): Promise<void> {
  e.preventDefault()
  spinner.classList.add('active')
  const body = new FormData(e.target as HTMLFormElement)

  // Add username to the form data
  body.append('username', username)
  body.append('session_id', sessionId);

  promptInput.value = ''
  promptInput.disabled = true

  const response = await fetch('/chat-messages/', { method: 'POST', body })
  await onFetchResponse(response)
}

// Attach event listener to the form
document.querySelector('form').addEventListener('submit', (e) => onSubmit(e).catch(onError))

// Load messages on page load
fetch(`/chat-messages/?username=${encodeURIComponent(username)}&session_id=${encodeURIComponent(sessionId)}`)
  .then(onFetchResponse)
  .catch(onError)
