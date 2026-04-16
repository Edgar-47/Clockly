import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';

class BusinessScreen extends StatelessWidget {
  const BusinessScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final businesses = state.session?.businesses ?? const [];

    return Scaffold(
      appBar: AppBar(title: const Text('Negocio')),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: businesses.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final business = businesses[index];
          return ListTile(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: BorderSide(color: Theme.of(context).dividerColor),
            ),
            title: Text(business.name),
            subtitle: Text('${business.type} · ${business.role ?? 'sin rol'}'),
            trailing: business.active ? const Icon(Icons.check_circle) : null,
            onTap: business.active || state.loading
                ? null
                : () => context.read<AppState>().switchBusiness(business.id),
          );
        },
      ),
    );
  }
}
