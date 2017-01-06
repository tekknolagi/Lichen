/* Native functions for Unicode operations.

Copyright (C) 2016 Paul Boddie <paul@boddie.org.uk>

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "native/common.h"
#include "types.h"
#include "exceptions.h"
#include "ops.h"
#include "progconsts.h"
#include "progops.h"
#include "progtypes.h"
#include "main.h"

static inline int boundary(char c)
{
    return ((c & 0xc0) == 0xc0) || !(c & 0x80);
}

static unsigned int nextpos(char *s, unsigned int size, unsigned int bytestart)
{
    unsigned int i = bytestart;

    while (i < size)
    {
        i++;
        if (boundary(s[i]))
            break;
    }

    return i;
}

static unsigned int prevpos(char *s, unsigned int bytestart)
{
    unsigned int i = bytestart;

    while (i > 0)
    {
        i--;
        if (boundary(s[i]))
            break;
    }

    return i;
}

/* Unicode operations. */

__attr __fn_native_unicode_unicode_len(__attr __args[])
{
    __attr * const _data = &__args[1];
    /* _data interpreted as string */
    char *s = _data->strvalue;
    unsigned int i, c = 0;

    for (i = 0; i < _data->size; i++)
        if (boundary(s[i]))
            c++;

    /* Return the new integer. */
    return __new_int(c);
}

__attr __fn_native_unicode_unicode_substr(__attr __args[])
{
    __attr * const _data = &__args[1];
    __attr * const start = &__args[2];
    __attr * const end = &__args[3];
    __attr * const step = &__args[4];
    /* _data interpreted as string */
    char *s = _data->strvalue, *sub;
    /* start.__data__ interpreted as int */
    int istart = __load_via_object(start->value, __pos___data__).intvalue;
    /* end.__data__ interpreted as int */
    int iend = __load_via_object(end->value, __pos___data__).intvalue;
    /* step.__data__ interpreted as int */
    int istep = __load_via_object(step->value, __pos___data__).intvalue;

    /* Calculate the number of characters. */
    size_t nchar = ((iend - istart - (istep > 0 ? 1 : -1)) / istep) + 1;
    unsigned int indexes[nchar];

    unsigned int c, d, i, to, from, lastbyte = 0;
    size_t resultsize = 0;

    /* Find the indexes of the characters. */
    if (istep > 0)
    {
        /* Get the first byte position. */
        for (c = 0; c < istart; c++)
            lastbyte = nextpos(s, _data->size, lastbyte);

        /* Get each subsequent byte position. */
        for (c = istart, i = 0; i < nchar; c += istep, i++)
        {
            indexes[i] = lastbyte;

            /* Add the character size to the result size. */
            resultsize += nextpos(s, _data->size, lastbyte) - lastbyte;

            for (d = c; d < c + istep; d++)
                lastbyte = nextpos(s, _data->size, lastbyte);
        }
    }
    else
    {
        /* Get the first byte position. */
        for (c = 0; c < istart; c++)
            lastbyte = nextpos(s, _data->size, lastbyte);

        /* Get each subsequent byte position. */
        for (c = istart, i = 0; i < nchar; c += istep, i++)
        {
            indexes[i] = lastbyte;

            /* Add the character size to the result size. */
            resultsize += nextpos(s, _data->size, lastbyte) - lastbyte;

            for (d = c; d > c + istep; d--)
                lastbyte = prevpos(s, lastbyte);
        }
    }

    /* Reserve space for a new string. */
    sub = (char *) __ALLOCATE(resultsize + 1, sizeof(char));

    /* Does not null terminate but final byte should be zero. */
    for (i = 0, to = 0; i < nchar; i++)
    {
        from = indexes[i];
        do
        {
            sub[to++] = s[from++];
        } while (!boundary(s[from]));
    }

    return __new_str(sub, resultsize);
}

/* Module initialisation. */

void __main_native_unicode()
{
}
