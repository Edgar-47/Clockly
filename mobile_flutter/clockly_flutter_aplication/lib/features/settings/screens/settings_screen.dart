import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/extensions/context_extensions.dart';
import '../../../shared/widgets/user_avatar.dart';
import '../../auth/providers/auth_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider).valueOrNull;
    final user = auth?.session?.userEntity;
    final business = auth?.session?.activeBusiness;

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 0,
            floating: true,
            backgroundColor: AppColors.background,
            title: Text('Configuración',
                style: Theme.of(context).textTheme.headlineSmall),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // Profile card
                if (user != null) ...[
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.primary, AppColors.accent],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      children: [
                        UserAvatar(
                          initials: user.initials,
                          imageUrl: user.avatarUrl,
                          size: 52,
                          color: Colors.white,
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                user.fullName,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 17,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              if (user.email != null)
                                Text(
                                  user.email!,
                                  style: const TextStyle(
                                      color: Colors.white70, fontSize: 13),
                                ),
                              const SizedBox(height: 4),
                              Text(
                                user.identifier,
                                style: const TextStyle(
                                    color: Colors.white70, fontSize: 13),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                ],

                // Active business
                if (business != null) ...[
                  const SizedBox(height: 8),
                  _SettingsTile(
                    icon: Icons.business_rounded,
                    title: business.name,
                    subtitle: 'Negocio activo',
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () => context.push('/business'),
                  ),
                ],

                const SizedBox(height: 24),
                _SectionTitle('Cuenta'),
                _SettingsTile(
                  icon: Icons.subscriptions_rounded,
                  title: 'Mi suscripción',
                  subtitle: 'Ver plan y límites',
                  onTap: () => context.push('/subscriptions'),
                ),
                _SettingsTile(
                  icon: Icons.tablet_rounded,
                  title: 'Modo kiosko',
                  subtitle: 'Fichaje en tablet/pantalla',
                  onTap: () => context.push('/kiosk'),
                ),

                const SizedBox(height: 24),
                _SectionTitle('Aplicación'),
                _SettingsTile(
                  icon: Icons.info_outline_rounded,
                  title: 'Versión',
                  subtitle: '1.0.0 (build 1)',
                ),
                _SettingsTile(
                  icon: Icons.privacy_tip_outlined,
                  title: 'Política de privacidad',
                  onTap: () {},
                ),

                const SizedBox(height: 24),
                _SettingsTile(
                  icon: Icons.logout_rounded,
                  title: 'Cerrar sesión',
                  titleColor: AppColors.error,
                  onTap: () async {
                    final confirmed = await context.showConfirmDialog(
                      title: 'Cerrar sesión',
                      message: '¿Estás seguro de que quieres salir?',
                      confirmLabel: 'Salir',
                      destructive: true,
                    );
                    if (confirmed == true) {
                      ref.read(authProvider.notifier).logout();
                    }
                  },
                ),

                const SizedBox(height: 40),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.title);
  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 0, 0, 8),
      child: Text(
        title.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              letterSpacing: 1.2,
              fontWeight: FontWeight.w700,
              color: AppColors.textHint,
            ),
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  const _SettingsTile({
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    this.onTap,
    this.titleColor,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;
  final Color? titleColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.neutral200),
      ),
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: (titleColor ?? AppColors.primary).withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon,
              size: 18, color: titleColor ?? AppColors.primary),
        ),
        title: Text(
          title,
          style: TextStyle(
              fontWeight: FontWeight.w500,
              color: titleColor ?? AppColors.textPrimary),
        ),
        subtitle: subtitle != null ? Text(subtitle!) : null,
        trailing: trailing ??
            (onTap != null
                ? const Icon(Icons.chevron_right_rounded,
                    color: AppColors.neutral400, size: 18)
                : null),
        onTap: onTap,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
