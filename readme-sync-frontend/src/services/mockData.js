// ---------------------------------------------------------------------------
// Données mockées — à remplacer par de vrais appels API (voir services/api.js)
// ---------------------------------------------------------------------------

export const mockUser = {
  id: 'u_1',
  name: 'Ilyaa',
  email: 'ilyaa@example.com',
  avatarInitials: 'IL',
}

export const mockRepositories = [
  {
    id: 'repo_1',
    fullName: 'ilyaa-digital/task-manager-api',
    description: 'API Flask pour la gestion de tâches',
    defaultBranch: 'main',
    trackedBranch: 'main',
    syncMode: 'auto',
    syncMethod: 'webhook',
    status: 'synced',
    lastSyncAt: '2026-08-07T09:12:00Z',
    connectedAt: '2026-05-02T10:00:00Z',
    readmeUpdatedCount: 14,
    pendingUpdates: 0,
  },
  {
    id: 'repo_2',
    fullName: 'ilyaa-digital/design-system',
    description: 'Composants UI partagés (React + Tailwind)',
    defaultBranch: 'main',
    trackedBranch: 'main',
    syncMode: 'manual',
    syncMethod: 'webhook',
    status: 'pending',
    lastSyncAt: '2026-08-06T18:40:00Z',
    connectedAt: '2026-03-11T08:20:00Z',
    readmeUpdatedCount: 9,
    pendingUpdates: 1,
  },
  {
    id: 'repo_3',
    fullName: 'ilyaa-digital/mobile-app',
    description: 'Application mobile React Native',
    defaultBranch: 'develop',
    trackedBranch: 'develop',
    syncMode: 'manual',
    syncMethod: 'polling',
    status: 'error',
    lastSyncAt: '2026-08-05T14:02:00Z',
    connectedAt: '2026-01-20T09:00:00Z',
    readmeUpdatedCount: 3,
    pendingUpdates: 1,
  },
  {
    id: 'repo_4',
    fullName: 'ilyaa-digital/infra-terraform',
    description: 'Infrastructure as code (AWS)',
    defaultBranch: 'main',
    trackedBranch: 'main',
    syncMode: 'auto',
    syncMethod: 'webhook',
    status: 'synced',
    lastSyncAt: '2026-08-07T07:55:00Z',
    connectedAt: '2026-06-18T11:00:00Z',
    readmeUpdatedCount: 6,
    pendingUpdates: 0,
  },
]

export const mockScans = [
  {
    id: 'scan_1',
    repositoryId: 'repo_1',
    repositoryName: 'ilyaa-digital/task-manager-api',
    sha: 'a3f9c21e8b4d0f6a1c2e3b4d5f60718293a4b5c',
    branch: 'main',
    author: 'karim.dev',
    message: 'feat: add Google OAuth authentication',
    affectedSections: ['features', 'installation', 'technologies'],
    impactCategory: 'feature',
    confidenceScore: 0.93,
    status: 'applied',
    createdAt: '2026-08-07T09:10:00Z',
  },
  {
    id: 'scan_2',
    repositoryId: 'repo_2',
    repositoryName: 'ilyaa-digital/design-system',
    sha: 'b7e2a19d3f4c5061728394a5b6c7d8e9f0a1b2c',
    branch: 'main',
    author: 'sara.ui',
    message: 'chore: bump storybook to v9',
    affectedSections: ['technologies'],
    impactCategory: 'dependency',
    confidenceScore: 0.71,
    status: 'pending_review',
    createdAt: '2026-08-06T18:38:00Z',
  },
  {
    id: 'scan_3',
    repositoryId: 'repo_3',
    repositoryName: 'ilyaa-digital/mobile-app',
    sha: 'c1d2e3f4a5b60718293a4b5c6d7e8f9a0b1c2d3',
    branch: 'develop',
    author: 'karim.dev',
    message: 'fix: crash on push notification permission',
    affectedSections: [],
    impactCategory: 'fix',
    confidenceScore: 0.4,
    status: 'error',
    createdAt: '2026-08-05T14:00:00Z',
  },
  {
    id: 'scan_4',
    repositoryId: 'repo_4',
    repositoryName: 'ilyaa-digital/infra-terraform',
    sha: 'd4e5f6a7b8c90123456789abcdef01234567890',
    branch: 'main',
    author: 'ilyaa',
    message: 'feat: add staging environment module',
    affectedSections: ['installation', 'description'],
    impactCategory: 'feature',
    confidenceScore: 0.88,
    status: 'applied',
    createdAt: '2026-08-07T07:50:00Z',
  },
]

export const mockPendingUpdates = [
  {
    id: 'pending_1',
    repositoryId: 'repo_2',
    repositoryName: 'ilyaa-digital/design-system',
    scanId: 'scan_2',
    createdAt: '2026-08-06T18:40:00Z',
    affectedSections: ['technologies'],
    sectionsDiff: {
      technologies: {
        before: '- React\n- Tailwind CSS\n- Storybook 8',
        after: '- React\n- Tailwind CSS\n- Storybook 9',
      },
    },
  },
  {
    id: 'pending_2',
    repositoryId: 'repo_3',
    repositoryName: 'ilyaa-digital/mobile-app',
    scanId: 'scan_3',
    createdAt: '2026-08-05T14:02:00Z',
    affectedSections: ['description'],
    sectionsDiff: {
      description: {
        before: 'Application mobile de gestion de tâches.',
        after:
          'Application mobile de gestion de tâches, avec notifications push et synchronisation hors-ligne.',
      },
    },
  },
]

export const mockScanDetails = {
  scan_1: {
    sectionsDiff: {
      features: {
        before: '- Login\n- Register',
        after: '- Login\n- Register\n- Google OAuth authentication',
      },
      installation: {
        before: 'pip install -r requirements.txt',
        after: 'pip install -r requirements.txt',
      },
      technologies: {
        before: '- Flask\n- SQLite',
        after: '- Flask\n- SQLite\n- Google OAuth (google-auth-oauthlib)',
      },
    },
    fileChanges: [
      { path: 'app/auth.py', type: 'added' },
      { path: 'requirements.txt', type: 'modified' },
    ],
  },
}

export const mockStats = {
  totalRepositories: mockRepositories.length,
  activeSyncs: mockRepositories.filter((r) => r.syncMode === 'auto').length,
  pendingUpdates: mockPendingUpdates.length,
  scansThisWeek: mockScans.length,
}

export const mockReadmeVersions = {
  repo_1: [
    { id: 'v3', versionNumber: 3, triggeredBy: 'sync_auto', createdAt: '2026-08-07T09:12:00Z' },
    { id: 'v2', versionNumber: 2, triggeredBy: 'manual_edit', createdAt: '2026-07-20T10:00:00Z' },
    { id: 'v1', versionNumber: 1, triggeredBy: 'initial_generation', createdAt: '2026-05-02T10:05:00Z' },
  ],
  repo_2: [
    { id: 'v2', versionNumber: 2, triggeredBy: 'manual_edit', createdAt: '2026-06-01T09:00:00Z' },
    { id: 'v1', versionNumber: 1, triggeredBy: 'initial_generation', createdAt: '2026-03-11T08:25:00Z' },
  ],
}

export const mockReadmeContent = {
  repo_1: `# task-manager-api\n\nAPI Flask pour la gestion de tâches.\n\n## Features\n- Login\n- Register\n- Google OAuth authentication\n\n## Installation\n\`\`\`\npip install -r requirements.txt\n\`\`\`\n\n## Technologies\n- Flask\n- SQLite\n- Google OAuth (google-auth-oauthlib)\n\n## License\nMIT\n`,
  repo_2: `# design-system\n\nComposants UI partagés (React + Tailwind).\n\n## Technologies\n- React\n- Tailwind CSS\n- Storybook 9\n`,
  repo_3: `# mobile-app\n\nApplication mobile de gestion de tâches.\n`,
  repo_4: `# infra-terraform\n\nInfrastructure as code (AWS).\n`,
}
