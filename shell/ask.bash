# Press Ctrl+G to replace the current bash line with a generated command.
_ask_widget() {
  local cmd
  cmd=$(ask --raw "$READLINE_LINE") || return
  READLINE_LINE="$cmd"
  READLINE_POINT=${#READLINE_LINE}
}

bind -x '"\C-g": _ask_widget'

