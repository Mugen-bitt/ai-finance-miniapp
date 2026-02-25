const tg = window.Telegram?.WebApp

export function useTelegram() {
  const onClose = () => {
    tg?.close()
  }

  const onToggleButton = () => {
    if (tg?.MainButton.isVisible) {
      tg.MainButton.hide()
    } else {
      tg?.MainButton.show()
    }
  }

  const showMainButton = (text, callback) => {
    if (tg) {
      tg.MainButton.text = text
      tg.MainButton.show()
      tg.MainButton.onClick(callback)
    }
  }

  const hideMainButton = () => {
    tg?.MainButton.hide()
  }

  const showBackButton = (callback) => {
    if (tg) {
      tg.BackButton.show()
      tg.BackButton.onClick(callback)
    }
  }

  const hideBackButton = () => {
    tg?.BackButton.hide()
  }

  const hapticFeedback = (type = 'impact', style = 'medium') => {
    if (tg?.HapticFeedback) {
      if (type === 'impact') {
        tg.HapticFeedback.impactOccurred(style)
      } else if (type === 'notification') {
        tg.HapticFeedback.notificationOccurred(style)
      }
    }
  }

  return {
    tg,
    user: tg?.initDataUnsafe?.user,
    initData: tg?.initData,
    isExpanded: tg?.isExpanded,
    colorScheme: tg?.colorScheme,
    onClose,
    onToggleButton,
    showMainButton,
    hideMainButton,
    showBackButton,
    hideBackButton,
    hapticFeedback
  }
}

export function initTelegram() {
  if (tg) {
    tg.ready()
    tg.expand()

    // Применяем тему Telegram
    document.documentElement.style.setProperty(
      '--tg-theme-bg-color',
      tg.themeParams.bg_color || '#ffffff'
    )
    document.documentElement.style.setProperty(
      '--tg-theme-text-color',
      tg.themeParams.text_color || '#000000'
    )
    document.documentElement.style.setProperty(
      '--tg-theme-hint-color',
      tg.themeParams.hint_color || '#999999'
    )
    document.documentElement.style.setProperty(
      '--tg-theme-link-color',
      tg.themeParams.link_color || '#2481cc'
    )
    document.documentElement.style.setProperty(
      '--tg-theme-button-color',
      tg.themeParams.button_color || '#2481cc'
    )
    document.documentElement.style.setProperty(
      '--tg-theme-button-text-color',
      tg.themeParams.button_text_color || '#ffffff'
    )
    document.documentElement.style.setProperty(
      '--tg-theme-secondary-bg-color',
      tg.themeParams.secondary_bg_color || '#f0f0f0'
    )
  }
}
