import { motion } from 'framer-motion'
import { Github, FileCode2, Sparkles, FileText } from 'lucide-react'

const nodes = [
  { icon: Github, label: 'Repository' },
  { icon: FileCode2, label: 'Code changes' },
  { icon: Sparkles, label: 'AI analysis' },
  { icon: FileText, label: 'README' },
]

export default function FlowDiagram({ active }) {
  return (
    <div style={styles.wrap} className="rs-flow-diagram">
      {nodes.map((node, i) => (
        <FlowStep key={node.label} node={node} index={i} active={active} isLast={i === nodes.length - 1} />
      ))}
    </div>
  )
}

function FlowStep({ node, index, active, isLast }) {
  const Icon = node.icon
  const nodeDelay = 0.15 + index * 0.28
  const lineDelay = nodeDelay + 0.18

  return (
    <div style={styles.step}>
      <div style={styles.nodeCol}>
        <motion.div
          initial={{ opacity: 0, scale: 0.6, y: 8 }}
          animate={active ? { opacity: 1, scale: 1, y: 0 } : {}}
          transition={{ delay: nodeDelay, duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          style={styles.node}
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={active ? { opacity: [0, 0.5, 0.25] } : {}}
            transition={{ delay: nodeDelay, duration: 1.2 }}
            style={styles.nodeGlow}
          />
          <Icon size={18} strokeWidth={2} style={{ position: 'relative', zIndex: 1 }} />
        </motion.div>
        <motion.span
          initial={{ opacity: 0, y: 4 }}
          animate={active ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: nodeDelay + 0.15, duration: 0.4 }}
          style={styles.label}
        >
          {node.label}
        </motion.span>
      </div>

      {!isLast && (
        <div style={styles.lineCol}>
          <motion.div
            initial={{ scaleX: 0 }}
            animate={active ? { scaleX: 1 } : {}}
            transition={{ delay: lineDelay, duration: 0.5, ease: 'easeOut' }}
            style={styles.line}
          />
          <motion.div
            initial={{ opacity: 0 }}
            animate={active ? { opacity: 1 } : {}}
            transition={{ delay: lineDelay + 0.5 }}
            style={styles.pulseTrack}
          >
            <div className="rs-flow-pulse-dot" style={styles.pulseDot} />
          </motion.div>
        </div>
      )}
    </div>
  )
}

const styles = {
  wrap: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'center',
    gap: 0,
    flexWrap: 'wrap',
  },
  step: {
    display: 'flex',
    alignItems: 'flex-start',
  },
  nodeCol: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: 84,
  },
  node: {
    width: 44,
    height: 44,
    borderRadius: 12,
    background: 'var(--bg-surface-raised)',
    border: '1px solid var(--accent-border)',
    color: 'var(--accent)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    flexShrink: 0,
  },
  nodeGlow: {
    position: 'absolute',
    inset: -6,
    borderRadius: 16,
    background: 'var(--accent)',
    filter: 'blur(14px)',
    zIndex: 0,
  },
  label: {
    fontSize: 11.5,
    fontWeight: 600,
    color: 'var(--text-tertiary)',
    marginTop: 10,
    textAlign: 'center',
    letterSpacing: '-0.01em',
  },
  lineCol: {
    position: 'relative',
    width: 56,
    height: 44,
    display: 'flex',
    alignItems: 'center',
    marginTop: 0,
  },
  line: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    background: 'linear-gradient(to right, var(--accent-border), var(--border-strong))',
    transformOrigin: 'left center',
  },
  pulseTrack: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 6,
    top: -2.5,
  },
  pulseDot: {
    position: 'absolute',
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: 'var(--accent)',
    boxShadow: '0 0 8px var(--accent)',
    animation: 'rs-flow-pulse 1.8s ease-in-out infinite',
  },
}
