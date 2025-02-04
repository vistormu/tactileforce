package ansi

// ANSI escape codes for cursor movement, text styling, and colors.
const (
	// Cursor movement
	Home  = "\x1b[H"
	Up    = "\x1b[A"
	Down  = "\x1b[B"
	Right = "\x1b[C"
	Left  = "\x1b[D"
	Start = "\r"

	// Screen clearing
	ScreenEnd   = "\x1b[0J"
	ScreenStart = "\x1b[1J"
	Screen      = "\x1b[2J"
	LineEnd     = "\x1b[0K"
	LineStart   = "\x1b[1K"
	Line        = "\x1b[2K"

	// Text styles
	Bold      = "\x1b[1m"
	Dim       = "\x1b[2m"
	Italic    = "\x1b[3m"
	Underline = "\x1b[4m"
	Blink     = "\x1b[5m"
	Reverse   = "\x1b[7m"
	Hidden    = "\x1b[8m"
	Strike    = "\x1b[9m"

	// Text colors
	Reset    = "\x1b[0m"
	Black    = "\x1b[30m"
	Red      = "\x1b[31m"
	Green    = "\x1b[32m"
	Yellow   = "\x1b[33m"
	Blue     = "\x1b[34m"
	Magenta  = "\x1b[35m"
	Cyan     = "\x1b[36m"
	White    = "\x1b[37m"
	Black2   = "\x1b[90m"
	Red2     = "\x1b[91m"
	Green2   = "\x1b[92m"
	Yellow2  = "\x1b[93m"
	Blue2    = "\x1b[94m"
	Magenta2 = "\x1b[95m"
	Cyan2    = "\x1b[96m"
	White2   = "\x1b[97m"

	// Background colors
	BgBlack    = "\x1b[40m"
	BgRed      = "\x1b[41m"
	BgGreen    = "\x1b[42m"
	BgYellow   = "\x1b[43m"
	BgBlue     = "\x1b[44m"
	BgMagenta  = "\x1b[45m"
	BgCyan     = "\x1b[46m"
	BgWhite    = "\x1b[47m"
	BgBlack2   = "\x1b[100m"
	BgRed2     = "\x1b[101m"
	BgGreen2   = "\x1b[102m"
	BgYellow2  = "\x1b[103m"
	BgBlue2    = "\x1b[104m"
	BgMagenta2 = "\x1b[105m"
	BgCyan2    = "\x1b[106m"
	BgWhite2   = "\x1b[107m"
)
