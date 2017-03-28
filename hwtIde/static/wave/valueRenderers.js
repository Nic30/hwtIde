function valCmp(a, b) {
	return (a[0] == b[0]) && (a[1] == b[1])
}
function valVal(a) {
	return a[0]
}
function valVld(a) {
	return a[1]
}
function mask(bits) {
	return (1 << bits) - 1
}
function renderBit(val, width) {
	if (val[0] == 1) {
		if (val[1])
			return "1"
		else
			return "0"
	} else {
		return "X"
	}
}
function renderBitsDec(val, width) {
	if (val[0] == mask(width)) {
		return val[0].toString()
	} else {
		return "X"
	}
}
function renderBitsHex(val, width) {
	var v = val[0].toString(16)
	var vld = val[1].toString(16)
	var chars = Math.ceil(width / 16)

	if (v.length < chars)
		v = "0".repeat(chars - v.length) + v

	for (var i = 0; i < chars; i++) {
		if (!(vld.length < i && vld[i] == 'f'))
			v[i] = 'X'
	}
	return "0x"+v
}
