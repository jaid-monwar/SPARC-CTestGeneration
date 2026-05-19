#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <ctype.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include <signal.h>
#include <time.h>
#include <errno.h>
#include <X11/Xos.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xresource.h>
#include <X11/Xproto.h>
#include <X11/Xatom.h>
#include <X11/cursorfont.h>
#include <X11/keysym.h>


// Function declarations
void show_usage(void);
void log_debug(const char * fmt);
Cursor get_cross_cursor(Display * display);
Window grab_mouse(Display * display, Window root_window);
void upgrab_mouse(Display * display);
Window select_window(Display * display, int * x, int * y);
Window findSubWindow(Display * display, Window top_window, Window window_to_check, int * x, int * y);
Window get_window_color(Display * display, XColor * color);
int MXError(Display * display, XErrorEvent * error);

#endif
