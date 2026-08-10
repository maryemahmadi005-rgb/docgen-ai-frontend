import { mockUser } from './mockData'

// ---------------------------------------------------------------------------
// Fausse authentification (mock). À remplacer plus tard par des appels à
// POST /api/auth/login, /api/auth/register, /api/auth/forgot-password
// via services/api.js. La forme des fonctions (async, retour { user, token })
// est déjà celle attendue une fois le backend Flask branché.
// ---------------------------------------------------------------------------

const FAKE_DELAY = 600

function delay(ms = FAKE_DELAY) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function loginMock({ email, password }) {
  await delay()
  if (!email || !password) {
    throw new Error('Email et mot de passe requis.')
  }
  if (password.length < 4) {
    throw new Error('Identifiants incorrects.')
  }
  const token = 'mock-token-' + btoa(email).slice(0, 16)
  const user = { ...mockUser, email }
  return { user, token }
}

export async function registerMock({ name, email, password }) {
  await delay()
  if (!name || !email || !password) {
    throw new Error('Tous les champs sont requis.')
  }
  const token = 'mock-token-' + btoa(email).slice(0, 16)
  const user = { ...mockUser, name, email, avatarInitials: initials(name) }
  return { user, token }
}

export async function forgotPasswordMock({ email }) {
  await delay()
  if (!email) throw new Error('Email requis.')
  return { message: `Si un compte existe pour ${email}, un lien a été envoyé.` }
}

function initials(name) {
  return name
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

/*
  Intégration future avec Flask (une fois le backend prêt) :

  export async function login({ email, password }) {
    return api.post('/auth/login', { email, password })
  }
  export async function register({ name, email, password }) {
    return api.post('/auth/register', { name, email, password })
  }
  export async function forgotPassword({ email }) {
    return api.post('/auth/forgot-password', { email })
  }
*/
