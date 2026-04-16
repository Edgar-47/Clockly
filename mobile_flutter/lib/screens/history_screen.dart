import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final dateFormat = DateFormat('dd/MM/yyyy HH:mm');

    return Scaffold(
      appBar: AppBar(title: const Text('Historial')),
      body: RefreshIndicator(
        onRefresh: state.refreshAttendance,
        child: ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: state.history.length,
          separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (context, index) {
            final session = state.history[index];
            return ListTile(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(color: Theme.of(context).dividerColor),
              ),
              title: Text(dateFormat.format(session.clockInTime)),
              subtitle: Text(
                session.clockOutTime == null
                    ? 'Sesion activa'
                    : 'Salida: ${dateFormat.format(session.clockOutTime!)}',
              ),
              trailing: Text(_duration(session.totalSeconds)),
            );
          },
        ),
      ),
    );
  }

  String _duration(int? seconds) {
    if (seconds == null) return '-';
    final hours = seconds ~/ 3600;
    final minutes = (seconds % 3600) ~/ 60;
    return '${hours}h ${minutes.toString().padLeft(2, '0')}m';
  }
}
