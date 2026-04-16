import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/app_state.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final user = state.session?.user;
    final business = state.session?.activeBusiness;

    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          CircleAvatar(
            radius: 36,
            child: Text(
              (user?.fullName.isNotEmpty == true ? user!.fullName[0] : 'C')
                  .toUpperCase(),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            user?.fullName ?? '',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 24),
          ListTile(
            title: const Text('DNI / Usuario'),
            subtitle: Text(user?.dni ?? ''),
          ),
          ListTile(
            title: const Text('Rol'),
            subtitle: Text(state.session?.activeBusinessRole ?? user?.role ?? ''),
          ),
          ListTile(
            title: const Text('Negocio activo'),
            subtitle: Text(business?.name ?? 'Sin negocio seleccionado'),
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: state.loading ? null : state.logout,
            icon: const Icon(Icons.logout),
            label: const Text('Cerrar sesion'),
          ),
        ],
      ),
    );
  }
}
