import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/utils/date_utils.dart';
import '../../../shared/extensions/context_extensions.dart';
import '../../../shared/widgets/brand_logo.dart';
import '../../attendance/providers/attendance_provider.dart';

class KioskScreen extends ConsumerStatefulWidget {
  const KioskScreen({super.key});

  @override
  ConsumerState<KioskScreen> createState() => _KioskScreenState();
}

class _KioskScreenState extends ConsumerState<KioskScreen> {
  Timer? _clockTicker;
  DateTime _now = DateTime.now();
  String _pin = '';
  bool _showPinEntry = false;
  bool _actionLoading = false;
  String? _message;
  bool _messageIsError = false;

  @override
  void initState() {
    super.initState();
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    _clockTicker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _now = DateTime.now());
    });
  }

  @override
  void dispose() {
    _clockTicker?.cancel();
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    SystemChrome.setPreferredOrientations(DeviceOrientation.values);
    super.dispose();
  }

  void _onPinDigit(String digit) {
    if (_pin.length >= 4) return;
    setState(() => _pin += digit);
    if (_pin.length == 4) {
      _processPin();
    }
  }

  void _onPinDelete() {
    if (_pin.isEmpty) return;
    setState(() => _pin = _pin.substring(0, _pin.length - 1));
  }

  Future<void> _processPin() async {
    setState(() => _actionLoading = true);
    // Simulate PIN validation: any 4-digit PIN triggers clock action
    await Future.delayed(const Duration(milliseconds: 600));
    final attendance = ref.read(attendanceProvider).valueOrNull;
    final isClockedIn = attendance?.isClockedIn ?? false;

    bool ok;
    if (isClockedIn) {
      ok = await ref.read(attendanceProvider.notifier).clockOut();
    } else {
      ok = await ref.read(attendanceProvider.notifier).clockIn();
    }

    if (mounted) {
      setState(() {
        _actionLoading = false;
        _pin = '';
        _showPinEntry = false;
        _message = ok
            ? (isClockedIn ? 'Salida registrada' : 'Entrada registrada')
            : 'Error al registrar';
        _messageIsError = !ok;
      });
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) setState(() => _message = null);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final attendance = ref.watch(attendanceProvider).valueOrNull;
    final isClockedIn = attendance?.isClockedIn ?? false;

    return Scaffold(
      backgroundColor: AppColors.neutral900,
      body: Stack(
        children: [
          // Background gradient
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),

          // Main content
          SafeArea(
            child: _showPinEntry
                ? _PinEntry(
                    pin: _pin,
                    loading: _actionLoading,
                    onDigit: _onPinDigit,
                    onDelete: _onPinDelete,
                    onCancel: () =>
                        setState(() {
                          _showPinEntry = false;
                          _pin = '';
                        }),
                  )
                : _KioskIdle(
                    now: _now,
                    isClockedIn: isClockedIn,
                    message: _message,
                    messageIsError: _messageIsError,
                    onAction: () =>
                        setState(() => _showPinEntry = true),
                    onExit: () => context.pop(),
                  ),
          ),
        ],
      ),
    );
  }
}

class _KioskIdle extends StatelessWidget {
  const _KioskIdle({
    required this.now,
    required this.isClockedIn,
    required this.message,
    required this.messageIsError,
    required this.onAction,
    required this.onExit,
  });

  final DateTime now;
  final bool isClockedIn;
  final String? message;
  final bool messageIsError;
  final VoidCallback onAction;
  final VoidCallback onExit;

  @override
  Widget build(BuildContext context) {
    final actionColor = isClockedIn ? AppColors.error : AppColors.success;
    final actionLabel = isClockedIn ? 'Registrar Salida' : 'Registrar Entrada';

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const ClocklyBrandLogo(
          variant: ClocklyLogoVariant.horizontal,
          markSize: 42,
          wordmarkSize: 30,
          inverse: true,
        ),
        const SizedBox(height: 32),
        // Clock
        Text(
          AppDateUtils.formatTime(now),
          style: const TextStyle(
            color: Colors.white,
            fontSize: 96,
            fontWeight: FontWeight.w800,
            letterSpacing: -4,
          ),
        ),
        Text(
          AppDateUtils.formatDateLong(now),
          style: const TextStyle(
            color: Colors.white60,
            fontSize: 20,
            fontWeight: FontWeight.w300,
          ),
        ),
        const SizedBox(height: 64),

        // Message
        if (message != null)
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            margin: const EdgeInsets.only(bottom: 24),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            decoration: BoxDecoration(
              color: messageIsError
                  ? AppColors.error.withOpacity(0.2)
                  : AppColors.success.withOpacity(0.2),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: messageIsError
                    ? AppColors.error.withOpacity(0.5)
                    : AppColors.success.withOpacity(0.5),
              ),
            ),
            child: Text(
              message!,
              style: TextStyle(
                color: messageIsError ? AppColors.error : AppColors.success,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),

        // Action button
        GestureDetector(
          onTap: onAction,
          child: Container(
            width: 280,
            height: 72,
            decoration: BoxDecoration(
              color: actionColor,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: actionColor.withOpacity(0.4),
                  blurRadius: 30,
                  offset: const Offset(0, 8),
                )
              ],
            ),
            child: Center(
              child: Text(
                actionLabel,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ),

        const SizedBox(height: 40),
        TextButton(
          onPressed: onExit,
          child: const Text('Salir del kiosko',
              style: TextStyle(color: Colors.white30, fontSize: 13)),
        ),
      ],
    );
  }
}

class _PinEntry extends StatelessWidget {
  const _PinEntry({
    required this.pin,
    required this.loading,
    required this.onDigit,
    required this.onDelete,
    required this.onCancel,
  });

  final String pin;
  final bool loading;
  final void Function(String) onDigit;
  final VoidCallback onDelete;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SizedBox(
        width: 320,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Introduce tu PIN',
                style: TextStyle(
                    color: Colors.white70,
                    fontSize: 20,
                    fontWeight: FontWeight.w300)),
            const SizedBox(height: 32),
            // Dots
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                4,
                (i) => Container(
                  margin: const EdgeInsets.symmetric(horizontal: 8),
                  width: 14,
                  height: 14,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: i < pin.length ? Colors.white : Colors.white24,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 40),

            if (loading)
              const CircularProgressIndicator(color: Colors.white)
            else
              _NumPad(onDigit: onDigit, onDelete: onDelete),

            const SizedBox(height: 20),
            TextButton(
              onPressed: onCancel,
              child: const Text('Cancelar',
                  style: TextStyle(color: Colors.white38)),
            ),
          ],
        ),
      ),
    );
  }
}

class _NumPad extends StatelessWidget {
  const _NumPad({required this.onDigit, required this.onDelete});
  final void Function(String) onDigit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (final row in [
          ['1', '2', '3'],
          ['4', '5', '6'],
          ['7', '8', '9'],
          ['', '0', '⌫'],
        ])
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: row.map((d) {
                if (d.isEmpty) return const SizedBox(width: 80);
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 10),
                  child: GestureDetector(
                    onTap: d == '⌫' ? onDelete : () => onDigit(d),
                    child: Container(
                      width: 64,
                      height: 64,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.08),
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white12),
                      ),
                      child: Center(
                        child: Text(
                          d,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.w400,
                          ),
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
      ],
    );
  }
}
