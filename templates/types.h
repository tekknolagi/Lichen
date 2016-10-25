/* Runtime types. */

#ifndef __TYPES_H__
#define __TYPES_H__

/* Attribute tables are lists of codes confirming the presence of attributes. */

typedef struct __table
{
    const unsigned int size, attrs[];
} __table;

/* Parameter tables are lists of codes confirming the presence of parameters, as
   well as the positions of those parameters in the list for a given function.
*/

typedef struct __param
{
    unsigned short code, pos;
} __param;

typedef struct __ptable
{
    const unsigned int size;
    const __param params[];
} __ptable;

/* Attributes are context and value pairs.
   Objects are collections of attributes.
   Object references are references to tables and collections of attributes.
   Attribute references are references to single attributes. */

typedef struct __obj __obj;

typedef struct __attr
{
    /* One of... */
    union
    {
        __obj * context;        /* attribute context */
        unsigned int min;       /* minimum number of parameters */
        __obj * b;              /* bound callable object */
    };

    /* One of... */
    union
    {
        __obj * value;          /* attribute value */
        const __ptable * ptable;/* parameter table */
        struct __attr (*fn)();  /* callable details */

        int intvalue;     	/* integer value */
        double floatvalue;	/* floating point value */
        char * strvalue;	/* string value */
    };
} __attr;

typedef struct __obj
{
    const __table * table;      /* attribute table */
    unsigned int pos;           /* position of attribute indicating class */
    __attr attrs[];             /* attributes */
} __obj;

typedef __obj * __ref;

/* Special instance position value. The pos member of __obj refers to the
   special type attribute for classes. For instances, it is set to zero. */

#define __INSTANCEPOS 0

/* Function pointer type. */

typedef __attr (*__func)();

/* Convenience macros. */

#define __ARGS(...) ((__attr[]) {__VA_ARGS__})
#define __KWARGS(...) ((__param[]) {__VA_ARGS__})

#endif /* __TYPES_H__ */
